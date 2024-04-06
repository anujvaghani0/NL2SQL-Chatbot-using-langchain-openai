import streamlit as st
from langchain_utils import invoke_chain
import re
import plotly.graph_objects as go

st.title("Langchain NL2SQL Chatbot")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# Initialize chat history
if "messages" not in st.session_state:
    # print("Creating session state")
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def generate_chart(response, chart_type):
    label_pattern = r'([A-Za-z]+):\s+(\d+)'
    matches = re.findall(label_pattern, response)
    labels = []
    sizes = []
    for match in matches:
        labels.append(match[0])
        sizes.append(int(match[1]))

    if chart_type == "Pie Chart":
        fig = go.Figure(data=[go.Pie(labels=labels, values=sizes)])
        fig.update_layout(title="Pie Chart", title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Line Chart":
        fig = go.Figure(data=go.Scatter(x=labels, y=sizes, mode='lines+markers'))
        fig.update_layout(title="Line Chart", xaxis_title="Label", yaxis_title="Size")
        st.plotly_chart(fig, use_container_width=True)


# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.spinner("Generating response..."):
        with st.chat_message("assistant"):
            response = invoke_chain(prompt, st.session_state.messages)
            print(response)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

    ch = st.selectbox("Select Chart Type", ["Line Chart", "Line Chart"])
    generate_chart(response, ch)
