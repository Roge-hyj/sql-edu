from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.ai_service import get_sql_hint, chat_with_teacher
from core.sql_judge import SQLJudgeService, SQLJudgeError, SQLSafetyError
from core.scaffolding import calculate_hint_level, get_ability_adjustment
from core.judge_setup import generate_init_sql_from_schema_preview, execute_setup_sql
from repository import QuestionRepository, SubmissionRepository, ChatRepository, UserRepository
from core.experience_service import compute_xp_gain, get_level_from_total
from schemas.submission import SubmissionCreate, SubmissionOut
from schemas.chat import ChatMessageOut, ChatSendIn, ChatSendOut
from dependencies import get_session
from core.auth import AuthHandler

router = APIRouter(prefix="/ai", tags=["ai"])
auth_handler = AuthHandler()


class SQLRequest(BaseModel):
    sql: str


class SQLCheckRequest(BaseModel):
    student_sql: str
    question_id: int  # 必须提供题目 ID
    language: str = "zh-CN"  # 回答语言：zh-CN(简体中文)、en(英文)、zh-TW(繁体中文)
    challenge_mode: bool = False  # 是否在限时挑战中完成，完成时给予额外经验


class SQLCheckResponse(BaseModel):
    is_correct: bool
    hint: dict  # SQLCheckResultSchema 的字典形式
    submission_id: int
    error_message: str | None = None
    is_safety_blocked: bool = False  # True 表示因危险操作被拒，而非结果不正确
    # 等级经验（仅首次正确完成该题时返回）
    earned_experience: int | None = None
    level_up: bool = False
    new_level: int | None = None


@router.post("/sql-hint")
async def sql_hint(payload: SQLRequest):
    """获取 SQL 提示（不进行判题，仅用于测试）。"""
    try:
        hint = await get_sql_hint(payload.sql)
        return {"hint": hint}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务调用失败: {str(e)}"
        )


@router.post("/check-sql", response_model=SQLCheckResponse)
async def check_sql(
    payload: SQLCheckRequest,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """检查学生提交的 SQL 是否正确，并生成 AI 教学提示。

    完整流程：
    1. 查询题目和标准答案
    2. 执行 SQL 判题
    3. 查询历史失败次数
    4. 计算支架等级
    5. 调用 AI 服务生成提示
    6. 保存提交记录
    """
    # 1. 查询题目
    question_repo = QuestionRepository(session)
    question = await question_repo.get_by_id(payload.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"题目 ID {payload.question_id} 不存在",
        )

    # 1.5 判题前自动建表：根据题目的 schema_preview 在判题库中创建表并插入示例数据，保证表存在且与题目约定一致
    init_sql = generate_init_sql_from_schema_preview(getattr(question, "schema_preview", None))
    if init_sql:
        await execute_setup_sql(session, init_sql)

    # 2. SQL 判题
    judge_service = SQLJudgeService(session)
    is_correct = False
    error_message = None
    is_safety_blocked = False

    try:
        required_cols = getattr(question, "required_output_columns", None)
        is_correct, error_message = await judge_service.judge_sql(
            payload.student_sql, question.correct_sql, required_output_columns=required_cols
        )
    except SQLSafetyError as e:
        error_message = str(e)
        is_correct = False
        is_safety_blocked = True
    except SQLJudgeError as e:
        error_message = str(e)
        is_correct = False

    # 3. 查询历史失败次数与用户整体表现；首次正确判断（发经验用）
    submission_repo = SubmissionRepository(session)
    failure_count = await submission_repo.get_failure_count(
        user_id, payload.question_id
    )
    correct_count_before = await submission_repo.get_correct_count(user_id, payload.question_id)
    stats = await submission_repo.get_user_overall_stats(user_id)
    ability_adj = get_ability_adjustment(stats["success_rate"], stats["total"])

    # 4. 计算支架等级（本题失败次数 + 根据能力动态调整）
    hint_level = calculate_hint_level(failure_count, ability_adj)

    # 4.5 对话条数（发经验前统计，不含本轮即将写入的 3 条）
    chat_repo = ChatRepository(session)
    chat_count_for_xp = await chat_repo.count_messages_for_user_question(user_id, payload.question_id)

    # 5. 调用 AI 服务生成提示（仅 AI 成功后才写入提交记录与对话，避免 AI 故障时误计一次提交）
    try:
        ai_hint_result = await get_sql_hint(
            student_sql=payload.student_sql,
            question_content=question.content,
            is_correct=is_correct,
            hint_level=hint_level,
            failure_count=failure_count,
            error_message=error_message,
            language=payload.language,
            is_safety_blocked=is_safety_blocked,
        )
    except Exception as e:
        # AI 服务故障：不写入提交记录，本次不计入尝试次数
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服务暂时不可用，本次未计入提交次数，请稍后重试。",
        ) from e

    # 将 AI 提示结果转换为字符串（存储到数据库）
    ai_hint_text = ai_hint_result.overall_comment

    # 6. 保存提交记录（仅 AI 成功后才执行到此）
    submission_data = SubmissionCreate(
        user_id=user_id,
        question_id=payload.question_id,
        student_sql=payload.student_sql,
        ai_hint=ai_hint_text,
        is_correct=is_correct,
        hint_level=hint_level,
    )
    submission = await submission_repo.create(submission_data)
    # 首次正确完成：发放经验并更新等级
    earned_experience = None
    level_up = False
    new_level = None
    if is_correct and correct_count_before == 0:
        xp = compute_xp_gain(
            question_difficulty=max(1, min(10, question.difficulty)),
            chat_count=chat_count_for_xp,
            wrong_attempts_before_correct=failure_count,
            challenge_mode=payload.challenge_mode,
        )
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if user is not None:
            prev_total = getattr(user, "total_experience", 0) or 0
            new_total = prev_total + xp
            user.total_experience = new_total
            prev_level, _, _ = get_level_from_total(prev_total)
            cur_level, _, xp_next = get_level_from_total(new_total)
            earned_experience = xp
            level_up = cur_level > prev_level
            new_level = cur_level if level_up else None
    # 同步写入“对话历史”，用于前端多轮对话展示与 AI 上下文
    if is_safety_blocked:
        system_result = "【新一轮提交】代码包含危险操作，系统已拒绝执行。"
    else:
        system_result = f"【新一轮提交】结果：{'正确' if is_correct else '不正确'}"
    await chat_repo.add_message(
        user_id=user_id,
        question_id=payload.question_id,
        role="system",
        content=system_result,
    )
    await chat_repo.add_message(
        user_id=user_id,
        question_id=payload.question_id,
        role="user",
        content=f"我提交的 SQL：\n\n```sql\n{payload.student_sql}\n```",
    )
    await chat_repo.add_message(
        user_id=user_id,
        question_id=payload.question_id,
        role="assistant",
        content=ai_hint_text,
    )

    await session.commit()

    # 7. 返回结果
    return SQLCheckResponse(
        is_correct=is_correct,
        hint=ai_hint_result.model_dump(),
        submission_id=submission.id,
        error_message=error_message,
        is_safety_blocked=is_safety_blocked,
        earned_experience=earned_experience,
        level_up=level_up,
        new_level=new_level,
    )


@router.get("/chat/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(
    question_id: int = Query(..., description="题目 ID"),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    chat_repo = ChatRepository(session)
    msgs = await chat_repo.list_messages(user_id=user_id, question_id=question_id, limit=limit)
    return msgs


@router.delete("/chat/messages")
async def clear_chat_messages(
    question_id: int = Query(..., description="题目 ID"),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """清除当前用户在该题目下的所有对话历史。"""
    chat_repo = ChatRepository(session)
    deleted = await chat_repo.delete_messages_by_user_question(user_id=user_id, question_id=question_id)
    await session.commit()
    return {"deleted": deleted}


@router.post("/chat", response_model=ChatSendOut)
async def chat(
    payload: ChatSendIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    # 题目上下文
    question_repo = QuestionRepository(session)
    question = await question_repo.get_by_id(payload.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"题目 ID {payload.question_id} 不存在",
        )

    # 最近一次提交（可选）
    submission_repo = SubmissionRepository(session)
    latest_list = await submission_repo.get_user_submissions(user_id, payload.question_id, limit=1)
    latest = latest_list[0] if latest_list else None

    # 失败次数与用户整体表现用于支架等级
    failure_count = await submission_repo.get_failure_count(user_id, payload.question_id)
    stats = await submission_repo.get_user_overall_stats(user_id)
    ability_adj = get_ability_adjustment(stats["success_rate"], stats["total"])
    hint_level = calculate_hint_level(failure_count, ability_adj)

    # 历史对话（仅 user/assistant 参与模型上下文）
    chat_repo = ChatRepository(session)
    history_msgs = await chat_repo.list_messages(user_id=user_id, question_id=payload.question_id, limit=50)
    history_for_llm = [
        {"role": m.role, "content": m.content}
        for m in history_msgs
        if m.role in ("user", "assistant")
    ]

    # 先写入用户消息
    await chat_repo.add_message(
        user_id=user_id,
        question_id=payload.question_id,
        role="user",
        content=payload.message,
    )

    # 调用 AI 继续对话
    reply = await chat_with_teacher(
        question_content=question.content,
        latest_student_sql=latest.student_sql if latest else None,
        latest_is_correct=latest.is_correct if latest else None,
        latest_error_message=None,  # 这里不重复传错误，AI 已可从对话与提示理解
        hint_level=hint_level,
        failure_count=failure_count,
        history=history_for_llm,
        user_message=payload.message,
        language=payload.language,
    )

    # 写入 AI 回复
    await chat_repo.add_message(
        user_id=user_id,
        question_id=payload.question_id,
        role="assistant",
        content=reply,
    )
    await session.commit()

    return ChatSendOut(reply=reply)


@router.get("/submissions", response_model=list[SubmissionOut])
async def get_my_submissions(
    question_id: int | None = Query(None, description="题目 ID（可选，过滤特定题目）"),
    limit: int = Query(100, ge=1, le=200, description="限制数量"),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """获取当前用户的提交记录。

    支持按题目 ID 过滤，返回按时间倒序排列的提交记录。
    """
    repo = SubmissionRepository(session)
    submissions = await repo.get_user_submissions(
        user_id, question_id, limit
    )
    return submissions


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    """获取单条提交记录详情。

    只能查看自己的提交记录。
    """
    repo = SubmissionRepository(session)
    submission = await repo.get_by_id(submission_id)
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"提交记录 ID {submission_id} 不存在"
        )
    
    # 验证是否是自己的提交记录
    if submission.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此提交记录"
        )
    
    return submission


__all__ = ["router"]





