import html
import aiohttp
import gradio as gr


BACKEND_URL = "http://localhost:8000"

BUDGET_MIN_LAKH = 1.0
BUDGET_MAX_LAKH = 100.0

PREFERENCE_CHOICES = ["Family Use", "Commercial", "Personal Use"]
PRIORITY_CHOICES = ["Mileage", "Performance"]


def format_budget(budget_lakh: float) -> str:
    if budget_lakh >= 100:
        return f"₹{budget_lakh / 100:.2f} Cr"
    return f"₹{budget_lakh:.1f} Lakh"


def _render_results(payload: dict, budget: float, preferences: list, priority: str) -> str:
    results = payload.get("results", [])
    count = payload.get("count", 0)

    header = (
        "### Your Preferences\n\n"
        f"- **Budget:** {format_budget(budget)}\n"
        f"- **Usage:** {', '.join(preferences)}\n"
        f"- **Priority:** {priority}\n\n"
        f"### 🚗 {count} Cars Found\n\n"
    )

    if not results:
        return header + "No cars match your criteria. Try widening your budget or preferences."

    cards = "<div style='display:flex; flex-wrap:wrap; gap:14px; margin-top:10px;'>"
    for car in results:
        brand = html.escape(car["brand"])
        model = html.escape(car["model"])
        variant = html.escape(car["variant"])
        body_type = html.escape(car["body_type"])
        price = f"₹{car['price_lakh']:.2f} Lakh"
        mileage = f"{car['mileage_kmpl']} kmpl"
        power = f"{car['power_bhp']} bhp"
        highlight = mileage if priority == "Mileage" else power

        cards += f"""
        <div style='
            background:#ffffff; border:1px solid #e5e7eb; border-radius:12px;
            padding:14px; width:230px; box-shadow:0 2px 8px rgba(0,0,0,0.07);
        '>
            <div style='font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.5px;'>{brand} · {body_type}</div>
            <div style='font-weight:700; font-size:15px; color:#111827; margin-top:2px;'>{model}</div>
            <div style='font-size:12px; color:#4b5563; margin-top:2px;'>{variant}</div>
            <div style='font-size:14px; color:#16a34a; font-weight:600; margin-top:8px;'>{price}</div>
            <div style='display:flex; gap:6px; margin-top:8px; font-size:11px; color:#374151;'>
                <span style='background:#f3f4f6; padding:3px 8px; border-radius:4px;'>⛽ {mileage}</span>
                <span style='background:#f3f4f6; padding:3px 8px; border-radius:4px;'>⚡ {power}</span>
            </div>
            <div style='margin-top:8px; font-size:11px; color:#667eea; font-weight:600;'>★ {highlight}</div>
        </div>"""
    cards += "</div>"

    sql = html.escape(payload.get("query", ""))
    params = html.escape(str(payload.get("params", [])))
    debug = (
        "<details style='margin-top:16px;'><summary style='cursor:pointer; color:#6b7280; font-size:12px;'>Show SQL</summary>"
        f"<pre style='background:#f9fafb; padding:10px; border-radius:6px; font-size:11px; overflow-x:auto;'>{sql}\n\n-- params: {params}</pre>"
        "</details>"
    )

    return header + cards + debug


async def submit_form(budget: float, preferences: list, priority: str):
    if not preferences:
        return "⚠️ Please select at least one preference."
    if not priority:
        return "⚠️ Please choose Mileage or Performance."

    payload = {
        "budget_lakh": float(budget),
        "preferences": preferences,
        "priority": priority,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/search-cars",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return f"⚠️ Backend error (HTTP {resp.status}): {body}"
                data = await resp.json()
    except aiohttp.ClientConnectorError:
        return f"⚠️ Cannot reach backend at {BACKEND_URL}. Start it with `uv run python backend.py`."
    except Exception as e:
        return f"⚠️ Request failed: {e}"

    return _render_results(data, budget, preferences, priority)


_CUSTOM_CSS = """
.pill-group .wrap {
    display: flex !important;
    flex-wrap: wrap;
    gap: 10px;
}
.pill-group label {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 999px;
    padding: 10px 20px;
    margin: 0;
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 500;
    user-select: none;
}
.pill-group label:hover {
    background: #e5e7eb;
    transform: translateY(-1px);
}
.pill-group label:has(input:checked) {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    border-color: transparent;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.35);
}
.pill-group label:has(input:checked) * {
    color: white !important;
}
.pill-group input[type="checkbox"],
.pill-group input[type="radio"] {
    display: none !important;
}
"""


def create_interface():
    with gr.Blocks(
        title="Car Buying Assistant",
        theme=gr.themes.Soft(),
        css=_CUSTOM_CSS,
    ) as iface:
        gr.Markdown("# 🚗 Car Buying Assistant")
        gr.Markdown("Answer 3 quick questions and we'll help you find the right car.")

        gr.Markdown("### 1. What's your budget?")
        budget = gr.Slider(
            minimum=BUDGET_MIN_LAKH,
            maximum=BUDGET_MAX_LAKH,
            value=10.0,
            step=0.5,
            label="Budget (in Lakhs ₹)",
        )

        gr.Markdown("### 2. What will you use the car for?")
        gr.Markdown("*Select all that apply*")
        preferences = gr.CheckboxGroup(
            choices=PREFERENCE_CHOICES,
            value=[],
            label="",
            show_label=False,
            elem_classes=["pill-group"],
        )

        gr.Markdown("### 3. What matters more to you?")
        priority = gr.Radio(
            choices=PRIORITY_CHOICES,
            value=None,
            label="",
            show_label=False,
            elem_classes=["pill-group"],
        )

        submit_btn = gr.Button("🔍 Find My Car", variant="primary", size="lg")

        output = gr.HTML(value="")

        submit_btn.click(
            submit_form,
            inputs=[budget, preferences, priority],
            outputs=output,
        )

    return iface


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7863,
        share=False,
        show_error=True,
    )
