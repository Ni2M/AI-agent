"""AI Agent
This script creates an AI agent and launches gradio user interface for
chatting with the agent and enquirying info and products recommendations.
This file can be run as the main file. It can also be imported as a module and contains the following
functions:

    * load_and_encode_image
    * run_agent
Example of importing in a jupyter notebook:
    >>>import app
    >>>app.demo.launch()
This will create the UI within the notebook. A local url will also be created to
use the UI in a browser.

Closing the launch:
    >>>app.demo.close()
or simply restart the kernel in the notebook.
"""
#%% import the necessarty packages.
import gradio as gr
import base64
import datetime
from dotenv import load_dotenv
_ = load_dotenv()
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
#%% Define Large language model
llm = init_chat_model("gpt-4o-mini", model_provider="openai")
#llm = init_chat_model("gpt-4.1", model_provider="openai")
#llm = init_chat_model("gpt-3.5-turbo", model_provider="openai") # does not accept image_url
#%% Define tools
tool1 = TavilySearchResults(max_results=4) #increased number of results
tool2 = TavilySearch(
    max_results=2,
    include_domains=['amazon.ca'] ,
    search_depth = 'advanced',
)
tools = [tool1, tool2]
#%% Define prompt
today = datetime.datetime.today().strftime("%A, %B %d, %Y")
prompt = f"""You are a smart shopping assistant. Your name is AI assistant. You can look up information.
Yo can recommend shoppers about products and help them make decision on shopping.
You are allowed to make multiple calls (either together or in sequence).
Only look up information when you are sure of what you want.
If you need to look up some information before asking a follow up question, you are allowed to do that.
Only when asked questions about products or recommending products use TavilySearch tool and search only on amazon.ca website, otherwise
for general questions about yourself or general topics use TavilySearchResults tool where you have access to various web resources.
For questions regarding today's date use {today}
"""
#%% an in-memory checkpointer, create the agent and config
memory = MemorySaver()
agent = create_react_agent(llm, tools, prompt=prompt, checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}
#%% # simple example:
"""
At this point for a simple example, we can invoke the agent to answer a question:
>>>message='What is your name?'
>>>result = agent.invoke({"messages": message},config)
>>>print(result['messages'][-1].content)
"""
#%% Define functions to use by UI

# function to load and encode the image
def load_and_encode_image(image_path):
    """
    This function takes in the path of the uploaded image, loads and encodes
    the binary data into Base64 and then decode it back to UTF-8.

    Parameters
    ----------
    image_path : str
        This is the filepath of the image.

    Returns
    -------
    str
        Decoded UTF-8 string. 
    Note: This can then be used for creating "image_url" to be passed to
    the created AI agent in run_agent function.

    Example
    -------
    Convert an image to decoded UTF-8 string

    >>> image_path = "red_shirt.jpg"
    >>> image_data = load_and_encode_image(image_path)

    """
    with open(image_path, "rb") as image_file:
        binary_data = image_file.read()
    return base64.b64encode(binary_data).decode("utf-8")

# function to run/invoke the agent
def run_agent(message, history):
    """
    This is a function that guides the response of the chatbot based on
    user "message" and "history" of the chat. Please note that here we are
    using the agent's memory, since .
    
    Note: history becomes important when dealing with simple functions or an LLM.
    For example, when invoking a langchain model only, we can append the messages in
    history to a list of chat history and pass it to the model.
    See as an example here <https://www.gradio.app/guides/chatinterface-examples#lang-chain>

    Parameters
    ----------
    message : dict(text: str, files: list[filepath])
        The input value representing the user's most recent message.
        When the user types in and/or attaches an image, message is captured
        in the "parameter_0" Multimodaltextbox component.
    history : list
        A list of openai-style dictionaries with role and content keys,
        representing the previous conversation history. 

    Returns
    -------
    Str
        The agent's final answer to the user's query. This could be a short
        answer to a question, a list of recommendations with links, or asking
        further questions for clarification.

    """
    if len(message['files'])==0:
        message_txt = message['text']
        result = agent.invoke({"messages": message_txt},config)
    else:
        image_path = message["files"][0]
        image_data = load_and_encode_image(image_path)
        messages_im = HumanMessage(
        content=[
            {"type": "text", "text": message["text"]},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ])
        result = agent.invoke({"messages": messages_im},config)
    return result['messages'][-1].content
#%% Create the agent's UI, Uses the run_agent function
demo = gr.ChatInterface(
    run_agent,
    type="messages",
    # Multimodal is used to allow image attachements
    multimodal=True,
    textbox=gr.MultimodalTextbox(file_count="single", file_types=["image"], sources=["upload"]),
    title="AI assistant",
    description="Hi there! Ask me any question!",
)
#%% 
if __name__ == "__main__":
    demo.launch()
#demo.close()







