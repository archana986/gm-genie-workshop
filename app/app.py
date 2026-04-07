"""
Manufacturing Genie — Databricks App
Powered by Genie Conversation API

Option B: Custom Gradio UI with manufacturing starter questions.

For a no-code path, use Option A: AI Playground → Genie tool → Export to Databricks App.
"""

import os
import gradio as gr
from databricks.sdk import WorkspaceClient

# --- Configuration ---
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")
APP_TITLE = "Manufacturing Genie"
APP_DESCRIPTION = (
    "Ask questions about OEE, quality, production events, and safety in plain English."
)

# Databricks branding
THEME = gr.themes.Soft(
    primary_hue=gr.themes.Color(
        c50="#fff5f3",
        c100="#ffe8e4",
        c200="#ffd1c9",
        c300="#ffb0a3",
        c400="#ff8a78",
        c500="#ff6b57",
        c600="#FF3621",
        c700="#e02d1a",
        c800="#b82515",
        c900="#8f1e10",
        c950="#4d0f08",
    ),
    neutral_hue="slate",
    font=["Inter", "system-ui", "sans-serif"],
)

CSS = """
.header-bar { background: #1B3139; padding: 16px 24px; border-radius: 8px; margin-bottom: 16px; }
.header-bar h1 { color: white; margin: 0; font-size: 22px; }
.header-bar p { color: #8899AA; margin: 4px 0 0 0; font-size: 13px; }
.starter-btn { border: 1px solid #e2e8f0 !important; border-radius: 8px !important; }
.footer { text-align: center; color: #94a3b8; font-size: 11px; margin-top: 12px; }
"""

# --- Genie Integration ---
w = WorkspaceClient()


def ask_genie(question: str, history: list) -> str:
    """Send a question to Genie and return the response."""
    if not GENIE_SPACE_ID:
        return "⚠️ GENIE_SPACE_ID not configured. Set it in app.yaml environment variables."

    try:
        response = w.genie.start_conversation(
            space_id=GENIE_SPACE_ID,
            content=question,
        )

        result = w.genie.get_message_query_result(
            space_id=GENIE_SPACE_ID,
            conversation_id=response.conversation_id,
            message_id=response.message_id,
        )

        if hasattr(result, "statement_response") and result.statement_response:
            sr = result.statement_response
            if hasattr(sr, "result") and sr.result:
                columns = (
                    [c.name for c in sr.result.schema.columns] if sr.result.schema else []
                )
                rows = []
                if sr.result.data_array:
                    for row in sr.result.data_array[:20]:
                        rows.append(" | ".join(str(v) for v in row))

                output = "**Query executed successfully**\n\n"
                if columns:
                    output += "| " + " | ".join(columns) + " |\n"
                    output += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                    for row in rows:
                        output += f"| {row} |\n"
                return output

        return "Genie processed your question. Check the Genie Space for the full response."

    except Exception as e:
        return (
            f"Error: {str(e)}\n\n"
            "Tip: Confirm GENIE_SPACE_ID, warehouse access, and UC grants for the app service principal."
        )


# --- Starter Questions (manufacturing) ---
STARTERS = [
    "What is average OEE by plant for the last year?",
    "Which production lines had the most downtime events last month?",
    "Show defect rate by shift for plant P01",
    "How many safety incidents were recorded by severity?",
    "Compare first-pass yield between two plants",
    "What are the top 3 plants by scrap rate?",
]


# --- Build UI ---
def create_app():
    with gr.Blocks(theme=THEME, css=CSS, title=APP_TITLE) as app:

        gr.HTML(
            f"""
        <div class="header-bar">
            <h1>🏭 {APP_TITLE}</h1>
            <p>{APP_DESCRIPTION}</p>
        </div>
        """
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=420,
                    type="messages",
                    show_copy_button=True,
                )
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask about OEE, quality, downtime, or safety…",
                        label="Your question",
                        scale=5,
                        lines=1,
                    )
                    send_btn = gr.Button("Ask Genie", variant="primary", scale=1)

            with gr.Column(scale=1):
                gr.Markdown("### Quick questions")
                for q in STARTERS:
                    btn = gr.Button(q, size="sm", elem_classes="starter-btn")
                    btn.click(
                        fn=lambda q=q: q,
                        outputs=msg,
                    )

        def respond(message, chat_history):
            if not message.strip():
                return "", chat_history
            chat_history = chat_history or []
            chat_history.append({"role": "user", "content": message})
            response = ask_genie(message, chat_history)
            chat_history.append({"role": "assistant", "content": response})
            return "", chat_history

        send_btn.click(respond, [msg, chatbot], [msg, chatbot])
        msg.submit(respond, [msg, chatbot], [msg, chatbot])

        gr.HTML(
            '<div class="footer">Powered by Databricks Genie | Data governed by Unity Catalog</div>'
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=8000)
