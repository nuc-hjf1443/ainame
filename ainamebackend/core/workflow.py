import asyncio
import json
import uuid
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

import settings
from core.tools import check_com_domain
from schemas.name_schemas import NameIn
from schemas.name_schemas import NameResultSchema


# 定义工作流状态。这个状态是工作流的参数。也可以叫数据清单。是伴随整个流程的
# TypedDict 把我们的python类进行字典校验
class WorkFlowState(TypedDict):
    user_id: int
    category: str
    surname: str
    gender: str
    length: str
    other: str
    exclude: List[str]
    final_output: Dict[str, Any]  # 用来存大模型生成的数据
    thread_id: str
    history_names: str


llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.5
)

# 告诉大模型，输出的格式是怎么的
structured_llm = llm.with_structured_output(NameResultSchema, method="json_mode")
NAMING_OUTPUT_SCHEMA = json.dumps(NameResultSchema.model_json_schema(), ensure_ascii=False)


async def invoke_naming_model(prompt: str, max_attempts: int = 3) -> NameResultSchema:
    """Invoke the naming model and reject empty structured responses."""
    last_error: Exception | None = None
    structured_prompt = (
        f"{prompt}\n\n"
        "请只返回符合以下 JSON Schema 的 JSON，不要输出 Markdown 或其他说明：\n"
        f"{NAMING_OUTPUT_SCHEMA}"
    )

    for attempt in range(max_attempts):
        try:
            response = await structured_llm.ainvoke(structured_prompt)
            if response is None:
                raise ValueError("大模型未返回结构化起名结果")

            result = NameResultSchema.model_validate(response)
            if not result.names:
                raise ValueError("大模型返回的候选名字为空")
            return result
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts - 1:
                await asyncio.sleep(0.5 * (attempt + 1))

    raise RuntimeError("大模型连续多次未返回有效的起名结果，请稍后重试") from last_error


# 定义工作流的节点  这是一个工作流的入口，负责转发任务
async def supervisor_node(state: WorkFlowState):
    """主管节点：后续可在这里扩展意图清洗或记录日志"""
    return {}


async def human_naming_node(state: WorkFlowState):
    """人名专家节点"""
    prompt = f"""你是一位精通汉语言文学与传统文化的命名专家。请为用户创作富有文化底蕴的人名。
        【姓氏】: {state['surname']}
        【性别倾向】: {state['gender']}
        【字数限制】: {state['length']}
        【其它具体要求】: {state['other']}
        【避讳排除字】: {'、'.join(state['exclude'])}
        原则：平仄协调，优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。请给出 5 个候选方案。"""

    response = await invoke_naming_model(prompt)
    return {"final_output": response.model_dump()}


from core.rag_service import retrive_user_from_knowledge


async def company_naming_node(state: WorkFlowState):
    """企业品牌节点"""
    user_id = state.get("user_id")
    search_query = state.get("other")

    # 1.查 通过用户的要求和useid查询语义数据库
    rag_context = retrive_user_from_knowledge(user_id, search_query)
    # 2.用
    prompt = f"""你是一位精通商业品牌传播的资深顾问。请创作符合商业规范的公司名。
    [用户需求]
    行业或者核心诉求: {state.get("other")}
    字数限制: {state['length']}
    避讳排除字: {'、'.join(state['exclude'])}

    【用户的专属私有知识库参考】
    {rag_context}

     原则：易于传播、符合行业调性，具备良好的商业愿景。请给出 5 个候选方案。"""

    response = await invoke_naming_model(prompt)
    memory_list = [f"【{n.name}】寓意：{n.moral}" for n in response.names]
    names_str = "\n".join(memory_list)

    tasks = [check_com_domain(n.domain) for n in response.names]
    statuses = await asyncio.gather(*tasks)

    for n, status in zip(response.names, statuses):
        n.domain_status = status


    # return {"final_output": response.model_dump()}
    #  "history_names": names_str}  主要是存到数据库，用来下次微调，从数据库中查询出来，给大模型，让他参考这些数据
    return {"final_output": response.model_dump(), "history_names": names_str}


async def pet_naming_node(state: WorkFlowState) -> Dict[str, Any]:
    """宠物起名节点"""
    prompt = f"""你是一位充满创意的宠物达人。请为用户的宠物起一些富有灵性的名字。
    【宠物特征/性格】: {state['other']}
    【字数限制】: {state['length']}
    【避讳排除字】: {'、'.join(state['exclude'])}

    原则：亲切好记、富有画面感或软萌感。请给出 5 个候选方案。"""
    response = await invoke_naming_model(prompt)
    return {"final_output": response.model_dump()}


# 节点都设计了有4个，如何组成工作流，如何流转
def route_by_category(state: WorkFlowState):
    """条件路由：根据前端传来的 category 决定走哪个节点"""
    category_map = {"人名": "human_node", "企业名": "company_node", "宠物名": "pet_node"}
    # 人名\企业名\宠物名
    category = state.get("category")
    # human\company\pet
    return category_map.get(category)


workflow = StateGraph(WorkFlowState)
# 第一个节点的名字是supervisor_node
workflow.add_node("supervisor_node", supervisor_node)
# 给起人名的节点起一个名字叫human
workflow.add_node("human", human_naming_node)
workflow.add_node("company", company_naming_node)
workflow.add_node("pet", pet_naming_node)

# 设置工作流的入口
workflow.set_entry_point("supervisor_node")

# 从入口进来后，如何走
workflow.add_conditional_edges("supervisor_node", route_by_category,
                               # { "条件路由函数的返回值" : "目标节点的名称" }
                               {"human_node": "human", "company_node": "company", "pet_node": "pet"})

workflow.add_edge("human", END)
workflow.add_edge("pet", END)
workflow.add_edge("company", END)

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

# 1. 全局初始化：只执行一次，复用连接
# thread_id 存入psotgress
DB_URI = settings.POSTGRES_MEMORY_URI

connection_pool = None
naming_graph = None


async def init_workflow_graph():
    """在 FastAPI 启动时调用此函数来初始化图和连接池"""
    global connection_pool, naming_graph
    connection_pool = AsyncConnectionPool(DB_URI, max_size=10, open=False)
    await connection_pool.open(wait=True)
    memory = AsyncPostgresSaver(connection_pool)
    # 编译带记忆的智能体
    naming_graph = workflow.compile(checkpointer=memory)


async def close_workflow_graph():
    """在 FastAPI 关闭时清理连接"""
    global connection_pool, naming_graph
    if connection_pool:
        await connection_pool.close()
    connection_pool = None
    naming_graph = None


# 完成起名流程的定义
# naming_graph = workflow.compile()

# 用户传过来的信息  告诉我给什么起名字，这些名字的对应要求有哪些
async def generate_naming(name_info: NameIn, user_id: int):
    workflowsatae = {
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {}
    }
    final_state = await  naming_graph.ainvoke(workflowsatae)
    return final_state["final_output"]


async def generate_naming_v2(name_info: NameIn, user_id: int):
    # 生成窗口id
    thread_id = str(uuid.uuid4())
    workflowsatae = {
        "thread_id": thread_id,
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {}
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await  naming_graph.ainvoke(workflowsatae, config)
    return {"thread_id": thread_id, "names": final_state["final_output"]}


from schemas.name_schemas import FeedbackSchema


async def feedback_names(name_info: FeedbackSchema, user_id: int):
    # 生成窗口id
    update_state = {
        "feedback": name_info.feedback,
        "category": name_info.category
    }
    config = {"configurable": {"thread_id": name_info.thread_id}}

    final_state = await  naming_graph.ainvoke(update_state, config)
    return {"thread_id": name_info.thread_id, "names": final_state["final_output"]}
