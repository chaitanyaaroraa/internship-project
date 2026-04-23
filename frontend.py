"""
Gradio frontend – CarDekho Recommendation Engine
=================================================
Collects 3-4 simple user inputs and sends them to the FastAPI backend
(POST http://127.0.0.1:8000/recommend) which runs a SQL query and
returns scored car recommendations.

Run:  python frontend.py          (starts on port 7860)
"""

import gradio as gr
import requests

# ──────────────────────────────────────────────────────────────
# Backend API URL
# ──────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/recommend"

# Model choices shown in the optional step 4
MODEL_CHOICES = [
    "Honda Amaze", "Honda City",
    "Hyundai Aura", "Hyundai Creta", "Hyundai i20", "Hyundai Venue",
    "Kia Sonet",
    "Mahindra XUV300", "Mahindra XUV700",
    "Maruti Alto K10", "Maruti Baleno", "Maruti Swift", "Maruti WagonR",
    "Tata Altroz", "Tata Nexon", "Tata Punch",
]


# ──────────────────────────────────────────────────────────────
# Call the FastAPI backend and render results as HTML cards
# ──────────────────────────────────────────────────────────────
def recommend_cars(budget, car_type, usage, preferred_models):
    """Send user preferences to the backend API and render the response."""

    preferred_models = preferred_models or []
    car_type = car_type or "Any"
    usage = usage or "Mixed"

    # Build request payload
    payload = {
        "budget": budget,
        "car_type": car_type,
        "usage": usage,
        "preferred_models": preferred_models,
    }

    # Call the FastAPI backend
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return """
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:48px; margin-bottom:16px;">⚠️</div>
            <h3 style="color:#e2e8f0; font-family:'Inter',sans-serif; margin:0 0 8px;
                        font-size:18px; font-weight:700;">
                Backend not reachable
            </h3>
            <p style="color:#94a3b8; font-family:'Inter',sans-serif; margin:0; font-size:13px;">
                Make sure the FastAPI server is running:<br>
                <code style="color:#818cf8;">python app.py</code> &nbsp;(port 8000)
            </p>
        </div>
        """
    except Exception as e:
        return f"""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:48px; margin-bottom:16px;">❌</div>
            <h3 style="color:#e2e8f0; font-family:'Inter',sans-serif; margin:0 0 8px;">Error</h3>
            <p style="color:#f87171; font-family:'Inter',sans-serif; font-size:13px;">{e}</p>
        </div>
        """

    cars = data.get("cars", [])
    count = data.get("count", 0)

    if not cars:
        return """
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:56px; margin-bottom:16px;">😔</div>
            <h3 style="color:#e2e8f0; font-family:'Inter',sans-serif; margin:0 0 8px;
                        font-size:20px; font-weight:700;">
                No cars match your criteria
            </h3>
            <p style="color:#94a3b8; font-family:'Inter',sans-serif; margin:0; font-size:14px;">
                Try increasing your budget or choosing a different car type.
            </p>
        </div>
        """

    stars_fn = lambda n: "⭐" * n + "☆" * (5 - n)

    cards_html = ""
    for idx, car in enumerate(cars):
        # Best-match badge for #1
        rank_badge = ""
        if idx == 0:
            rank_badge = """
            <div style="
                position:absolute; top:12px; left:12px;
                background:linear-gradient(135deg, #f59e0b, #f97316);
                color:#fff; font-size:11px; font-weight:800;
                padding:5px 12px; border-radius:20px;
                font-family:'Inter',sans-serif; letter-spacing:0.5px;
                box-shadow:0 4px 12px rgba(245,158,11,0.4);
            ">🏆 BEST MATCH</div>
            """

        price_display = f"₹{car['price_lakh']:.1f}L"
        on_road_lakh = round(car["on_road_price"] / 100000, 1)

        cards_html += f"""
        <div style="
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 18px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        " onmouseover="this.style.transform='translateY(-6px)';this.style.boxShadow='0 20px 40px rgba(99,102,241,0.18)'"
           onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='none'">

            <!-- Header with price badge -->
            <div style="position:relative; background:linear-gradient(135deg, #1a1f3a, #0f172a);
                        padding:20px 20px 16px;">
                {rank_badge}
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <h3 style="margin:0 0 2px; color:#f1f5f9; font-family:'Inter',sans-serif;
                                   font-size:19px; font-weight:700;">
                            {car['model']}
                        </h3>
                        <p style="margin:0; color:#818cf8; font-family:'Inter',sans-serif;
                                  font-size:12px; font-weight:600; text-transform:uppercase;
                                  letter-spacing:1.2px;">
                            {car['variant']}
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <div style="
                            background: linear-gradient(135deg, #6366f1, #8b5cf6);
                            color:#fff; font-size:13px; font-weight:700;
                            padding:6px 14px; border-radius:20px;
                            font-family:'Inter',sans-serif;
                            box-shadow:0 4px 12px rgba(99,102,241,0.4);
                        ">{price_display}</div>
                        <div style="color:#64748b; font-size:10px; font-family:'Inter',sans-serif;
                                    margin-top:4px;">On-road ₹{on_road_lakh}L</div>
                    </div>
                </div>
            </div>

            <!-- Card body -->
            <div style="padding:16px 20px 18px;">

                <!-- Specs pill -->
                <div style="margin-bottom:14px;">
                    <span style="background:#0f172a; color:#94a3b8; font-size:11px;
                                 padding:5px 12px; border-radius:20px; font-family:'Inter',sans-serif;
                                 border:1px solid #1e293b;">
                        {car['specs']}
                    </span>
                </div>

                <!-- Stats grid -->
                <div style="display:flex; gap:8px; margin-bottom:12px;">
                    <div style="flex:1; background:#0f172a; padding:10px 12px; border-radius:10px;
                                text-align:center;">
                        <div style="color:#94a3b8; font-size:10px; font-family:'Inter',sans-serif;
                                    margin-bottom:3px; letter-spacing:0.5px;">MILEAGE</div>
                        <div style="color:#e2e8f0; font-size:15px; font-weight:700;
                                    font-family:'Inter',sans-serif;">
                            {car['mileage_kmpl']}
                            <span style="font-size:11px; font-weight:400; color:#94a3b8;">km/l</span>
                        </div>
                    </div>
                    <div style="flex:1; background:#0f172a; padding:10px 12px; border-radius:10px;
                                text-align:center;">
                        <div style="color:#94a3b8; font-size:10px; font-family:'Inter',sans-serif;
                                    margin-bottom:3px; letter-spacing:0.5px;">SAFETY</div>
                        <div style="font-size:13px; line-height:1;">
                            {stars_fn(car['safety_rating'])}
                        </div>
                    </div>
                    <div style="flex:1; background:#0f172a; padding:10px 12px; border-radius:10px;
                                text-align:center;">
                        <div style="color:#94a3b8; font-size:10px; font-family:'Inter',sans-serif;
                                    margin-bottom:3px; letter-spacing:0.5px;">CITY</div>
                        <div style="color:#e2e8f0; font-size:13px; font-weight:600;
                                    font-family:'Inter',sans-serif;">
                            {car['city']}
                        </div>
                    </div>
                </div>

                <!-- Features -->
                <div style="margin-bottom:14px;">
                    <div style="color:#94a3b8; font-size:10px; font-family:'Inter',sans-serif;
                                margin-bottom:4px; letter-spacing:0.5px; font-weight:600;">FEATURES</div>
                    <div style="color:#cbd5e1; font-size:12px; font-family:'Inter',sans-serif;">
                        {car['features']}
                    </div>
                </div>

                <!-- Why it fits -->
                <div style="
                    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
                    border-left: 3px solid #6366f1;
                    border-radius: 0 10px 10px 0;
                    padding: 10px 14px;
                ">
                    <div style="color:#94a3b8; font-size:10px; font-family:'Inter',sans-serif;
                                margin-bottom:3px; letter-spacing:0.5px; font-weight:600;">
                        WHY IT FITS
                    </div>
                    <div style="color:#cbd5e1; font-size:13px; font-family:'Inter',sans-serif;
                                line-height:1.45;">
                        {car['reason']}
                    </div>
                </div>
            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom:18px; text-align:center;">
        <p style="color:#94a3b8; font-family:'Inter',sans-serif; font-size:14px; margin:0;">
            Found <strong style="color:#818cf8;">{count}</strong> car{'s' if count != 1 else ''}
            matching your preferences
            <span style="color:#334155; margin:0 6px;">|</span>
            <span style="color:#64748b; font-size:12px;">powered by SQL query via FastAPI</span>
        </p>
    </div>
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        padding: 0 0 10px;
    ">
        {cards_html}
    </div>
    """


# ──────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* Global */
.gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(160deg, #0a0e1a 0%, #101828 50%, #0c1220 100%) !important;
    min-height: 100vh;
    max-width: 960px !important;
    margin: 0 auto !important;
}
footer { display: none !important; }

/* Hero */
#hero-section {
    text-align: center;
    padding: 48px 20px 8px;
}

/* Step cards */
.step-card {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%) !important;
    border: 1px solid #334155 !important;
    border-radius: 18px !important;
    padding: 28px 28px 24px !important;
}

/* Step numbers */
.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 50%;
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    margin-right: 10px;
    flex-shrink: 0;
}

/* Slider */
input[type="range"] { accent-color: #6366f1 !important; }

/* Radio / checkbox groups */
.gr-radio label, .gr-checkbox-group label {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    color: #e2e8f0 !important;
    transition: all 0.25s ease !important;
    font-family: 'Inter', sans-serif !important;
}
.gr-radio label:hover, .gr-checkbox-group label:hover {
    border-color: #6366f1 !important;
    box-shadow: 0 0 14px rgba(99,102,241,0.15) !important;
}

/* Primary button */
.primary-btn {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    padding: 15px 56px !important;
    color: #fff !important;
    letter-spacing: 0.5px;
    box-shadow: 0 8px 28px rgba(99,102,241,0.35) !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
}
.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 36px rgba(99,102,241,0.5) !important;
}

/* Results area */
#results-area { min-height: 180px; }

/* Footer */
#footer-bar { text-align: center; padding: 24px 20px 16px; }
#footer-bar p {
    color: #475569;
    font-size: 12px;
    margin: 0;
    font-family: 'Inter', sans-serif;
}
"""


# ──────────────────────────────────────────────────────────────
# Build the Gradio UI
# ──────────────────────────────────────────────────────────────
with gr.Blocks(title="CarDekho – Find Your Perfect Car") as demo:

    # ── Hero ──────────────────────────────────────────────────
    gr.HTML("""
    <div id="hero-section">
        <div style="font-size:52px; margin-bottom:8px;">🚗</div>
        <h1 style="
            font-size:38px; font-weight:900; margin:0 0 6px;
            background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #f472b6 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing:-0.5px; font-family:'Inter',sans-serif;
        ">Find Your Perfect Car</h1>
        <p style="color:#94a3b8; font-size:15px; margin:0; font-family:'Inter',sans-serif;">
            Answer a few quick questions — our backend queries the database and finds the best match.
        </p>
    </div>
    """)

    gr.HTML("<div style='height:20px'></div>")

    # ── Step 1 – Budget ───────────────────────────────────────
    with gr.Group(elem_classes=["step-card"]):
        gr.HTML("""
        <div style="display:flex; align-items:center; margin-bottom:14px;">
            <span class="step-number">1</span>
            <span style="color:#e2e8f0; font-size:16px; font-weight:700;
                         font-family:'Inter',sans-serif;">
                What's your budget?
            </span>
        </div>
        """)
        budget_slider = gr.Slider(
            minimum=3, maximum=25, value=12, step=0.5,
            label="Budget (in Lakhs ₹)",
            info="Drag to set your maximum ex-showroom budget",
        )

    gr.HTML("<div style='height:12px'></div>")

    # ── Step 2 – Car type ─────────────────────────────────────
    with gr.Group(elem_classes=["step-card"]):
        gr.HTML("""
        <div style="display:flex; align-items:center; margin-bottom:14px;">
            <span class="step-number">2</span>
            <span style="color:#e2e8f0; font-size:16px; font-weight:700;
                         font-family:'Inter',sans-serif;">
                What type of car do you prefer?
            </span>
        </div>
        """)
        car_type_input = gr.Radio(
            choices=["Any", "SUV", "Sedan", "Hatchback"],
            value="Any",
            label="Car Type",
            info="Pick the body style you like",
        )

    gr.HTML("<div style='height:12px'></div>")

    # ── Step 3 – Usage ────────────────────────────────────────
    with gr.Group(elem_classes=["step-card"]):
        gr.HTML("""
        <div style="display:flex; align-items:center; margin-bottom:14px;">
            <span class="step-number">3</span>
            <span style="color:#e2e8f0; font-size:16px; font-weight:700;
                         font-family:'Inter',sans-serif;">
                Where will you drive the most?
            </span>
        </div>
        """)
        usage_input = gr.Radio(
            choices=["City", "Highway", "Mixed"],
            value="Mixed",
            label="Primary Usage",
            info="This helps us match driving conditions",
        )

    gr.HTML("<div style='height:12px'></div>")

    # ── Step 4 (optional) – Preferred models ──────────────────
    with gr.Group(elem_classes=["step-card"]):
        gr.HTML("""
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <span class="step-number">4</span>
            <span style="color:#e2e8f0; font-size:16px; font-weight:700;
                         font-family:'Inter',sans-serif;">
                Any models you already like?
            </span>
            <span style="
                background:#1e293b; color:#64748b; font-size:10px; font-weight:600;
                padding:3px 10px; border-radius:20px; margin-left:10px;
                font-family:'Inter',sans-serif; letter-spacing:0.5px;
            ">OPTIONAL</span>
        </div>
        <p style="color:#64748b; font-size:12px; margin:0 0 12px 38px; font-family:'Inter',sans-serif;">
            Select if you already have a few models in mind — we'll prioritise them.
        </p>
        """)
        model_input = gr.CheckboxGroup(
            choices=MODEL_CHOICES,
            label="Preferred Models",
        )

    gr.HTML("<div style='height:20px'></div>")

    # ── Submit ────────────────────────────────────────────────
    with gr.Row():
        gr.Column()
        with gr.Column():
            submit_btn = gr.Button(
                "🔍  Show My Recommendations",
                variant="primary",
                elem_classes=["primary-btn"],
            )
        gr.Column()

    gr.HTML("<div style='height:24px'></div>")

    # ── Results ───────────────────────────────────────────────
    results_html = gr.HTML(
        value="""
        <div style="text-align:center; padding:50px 20px;">
            <div style="font-size:44px; margin-bottom:10px;">🔎</div>
            <p style="color:#64748b; font-family:'Inter',sans-serif; font-size:14px; margin:0;">
                Set your preferences above and hit
                <strong style="color:#818cf8;">Show My Recommendations</strong>
            </p>
        </div>
        """,
        elem_id="results-area",
    )

    # ── Footer ────────────────────────────────────────────────
    gr.HTML("""
    <div id="footer-bar">
        <p>Made with ❤️ · CarDekho Recommendation Engine · Gradio + FastAPI + SQLite</p>
    </div>
    """)

    # ── Wire up ───────────────────────────────────────────────
    submit_btn.click(
        fn=recommend_cars,
        inputs=[budget_slider, car_type_input, usage_input, model_input],
        outputs=results_html,
    )


# ──────────────────────────────────────────────────────────────
# Launch
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(css=CUSTOM_CSS, theme=gr.themes.Base())
