import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from tools import all_tools

llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

FINANCIAL_AGENT_SYSTEM_PROMPT = """You are a financial research analyst assistant with access to the following tools:

- get_stock_price: real-time stock price and daily change for a ticker
- search_recent_news: recent news/events about a company
- query_company_filing: retrieves specific facts and figures from an uploaded official filing (10-K, earnings report)
- calculate_financial_ratio: precise calculation of net income and profit margin from revenue/expenses

Guidelines for using these tools:
- Only call the tools that are actually needed to answer the question.
- Prefer query_company_filing over your own knowledge for any specific financial figures -- never estimate or guess numbers.
- Use calculate_financial_ratio whenever a calculation is required, instead of computing it yourself.
- Use search_recent_news for qualitative context, not for hard numbers.
- If a tool returns no useful information, say so plainly instead of filling the gap with assumptions.
- Do not fabricate data.
- Keep your final answer factual and neutral. Frame recommendations as analysis, not instructions to buy/sell.
- If the user's question is narrow, answer directly without unnecessary tool calls."""

# Step 1: the ReAct agent -- decides which tools to call, in what order,
# based on reasoning about the user's question.
agent = create_react_agent(llm, all_tools, prompt=FINANCIAL_AGENT_SYSTEM_PROMPT)

# Step 2: a sequential chain (LCEL) that takes the agent's raw findings
# and reformats them into a clean, structured report.
report_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a financial analyst assistant. Turn the raw research notes below "
     "into a clean, structured investment report with these sections: "
     "Summary, Key Financials, Risks, Recommendation. "
     "Be concise and use bullet points where helpful."),
    ("human", "Raw findings:\n{findings}")
])

report_chain = report_prompt | llm | StrOutputParser()


def run_financial_analysis(question: str) -> dict:
    """
    Full pipeline: agent gathers findings using tools it decides to call,
    then the sequential chain formats those findings into a final report.
    """
    agent_result = agent.invoke({"messages": [("human", question)]})
    raw_findings = agent_result["messages"][-1].content

    final_report = report_chain.invoke({"findings": raw_findings})

    return {
        "raw_findings": raw_findings,
        "report": final_report,
    }