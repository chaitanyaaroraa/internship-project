"""
Gradio frontend - CarDekho Recommendation Engine
=================================================
Compact, CarDekho-branded UI (orange + white).
Sends user inputs to FastAPI backend and renders results.

Run:  python frontend.py
"""

import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000/recommend"

BRAND_CHOICES = ["Maruti", "Hyundai", "Tata", "Honda", "Kia", "Mahindra"]


# ──────────────────────────────────────────────────────────────
# Call backend and render HTML cards
# ──────────────────────────────────────────────────────────────
def recommend_cars(budget, car_type, usage, preferred_brands):
    preferred_brands = preferred_brands or []
    car_type = car_type or "Any"
    usage = usage or "Mixed"

    payload = {
        "budget": budget,
        "car_type": car_type,
        "usage": usage,
        "preferred_brands": preferred_brands,
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return """
        <div style="text-align:center; padding:40px 20px;">
            <div style="font-size:40px; margin-bottom:12px;">&#9888;</div>
            <h3 style="color:#333; font-family:'Inter',sans-serif; margin:0 0 6px; font-size:16px;">
                Backend not reachable
            </h3>
            <p style="color:#888; font-family:'Inter',sans-serif; margin:0; font-size:13px;">
                Start the FastAPI server first: <code style="color:#ff6b00;">python app.py</code>
            </p>
        </div>
        """
    except Exception as e:
        return f"""
        <div style="text-align:center; padding:40px 20px;">
            <h3 style="color:#333; font-family:'Inter',sans-serif;">Error</h3>
            <p style="color:#d32f2f; font-family:'Inter',sans-serif; font-size:13px;">{e}</p>
        </div>
        """

    cars = data.get("cars", [])
    count = data.get("count", 0)

    if not cars:
        return """
        <div style="text-align:center; padding:40px 20px;">
            <div style="font-size:40px; margin-bottom:10px;">&#128542;</div>
            <h3 style="color:#333; font-family:'Inter',sans-serif; margin:0 0 6px; font-size:16px;">
                No cars match your criteria
            </h3>
            <p style="color:#888; font-family:'Inter',sans-serif; margin:0; font-size:13px;">
                Try increasing your budget or changing the car type.
            </p>
        </div>
        """

    stars_fn = lambda n: '<span style="color:#ff6b00;">' + ("&#9733;" * n) + "</span>" + '<span style="color:#ddd;">' + ("&#9733;" * (5 - n)) + "</span>"

    cards_html = ""
    for idx, car in enumerate(cars):
        badge = ""
        if idx == 0:
            badge = """<span style="
                background:#ff6b00; color:#fff; font-size:10px; font-weight:700;
                padding:3px 10px; border-radius:12px; font-family:'Inter',sans-serif;
                letter-spacing:0.3px; margin-left:8px; vertical-align:middle;
            ">BEST MATCH</span>"""

        on_road = round(car["on_road_price"] / 100000, 1)

        cards_html += f"""
        <div style="
            background:#fff; border:1px solid #e8e8e8; border-radius:12px;
            overflow:hidden; transition:box-shadow 0.2s ease;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);
        " onmouseover="this.style.boxShadow='0 6px 20px rgba(255,107,0,0.12)'"
           onmouseout="this.style.boxShadow='0 1px 4px rgba(0,0,0,0.06)'">
            <div style="padding:14px 16px 12px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <div>
                        <div style="display:flex; align-items:center;">
                            <span style="font-size:15px; font-weight:700; color:#222;
                                         font-family:'Inter',sans-serif;">{car['model']}</span>
                            {badge}
                        </div>
                        <span style="color:#ff6b00; font-size:11px; font-weight:600;
                                     font-family:'Inter',sans-serif;">{car['variant']}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="background:#ff6b00; color:#fff; font-size:12px; font-weight:700;
                                    padding:4px 10px; border-radius:16px; font-family:'Inter',sans-serif;
                        ">Rs {car['price_lakh']}L</div>
                        <div style="color:#999; font-size:9px; font-family:'Inter',sans-serif;
                                    margin-top:2px;">On-road Rs {on_road}L</div>
                    </div>
                </div>
                <div style="display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
                    <span style="background:#fff5ee; color:#ff6b00; font-size:10px; font-weight:600;
                                 padding:3px 8px; border-radius:10px; font-family:'Inter',sans-serif;">
                        {car['mileage_kmpl']} km/l
                    </span>
                    <span style="background:#fff5ee; color:#ff6b00; font-size:10px; font-weight:600;
                                 padding:3px 8px; border-radius:10px; font-family:'Inter',sans-serif;">
                        {stars_fn(car['safety_rating'])}
                    </span>
                    <span style="background:#f5f5f5; color:#666; font-size:10px; font-weight:500;
                                 padding:3px 8px; border-radius:10px; font-family:'Inter',sans-serif;">
                        {car['specs']}
                    </span>
                </div>
                <div style="background:#fff9f5; border-left:3px solid #ff6b00; padding:6px 10px;
                            border-radius:0 8px 8px 0;">
                    <span style="color:#222; font-size:11px; font-family:'Inter',sans-serif;
                                 line-height:1.4;">{car['reason']}</span>
                </div>
            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom:12px;">
        <span style="color:#666; font-family:'Inter',sans-serif; font-size:13px;">
            Found <strong style="color:#ff6b00;">{count}</strong> car{'s' if count != 1 else ''} for you
            <span style="color:#ccc; margin:0 6px;">|</span>
            <span style="color:#aaa; font-size:11px;">via SQL query</span>
        </span>
    </div>
    <div style="display:flex; flex-direction:column; gap:12px;">
        {cards_html}
    </div>
    """


# ──────────────────────────────────────────────────────────────
# CarDekho-themed CSS (orange + white, compact)
# ──────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: #f5f5f5 !important;
    min-height: 100vh;
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 0 !important;
}
footer { display: none !important; }

/* Header bar */
#cd-header {
    background: #ff6b00;
    padding: 14px 24px;
    border-radius: 0 0 16px 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(255,107,0,0.2);
}

/* Filters panel */
.filters-panel {
    background: #fff !important;
    border: 1px solid #eee !important;
    border-radius: 14px !important;
    padding: 20px 24px 16px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04) !important;
}

/* Labels */
.filters-panel label span {
    color: #333 !important;
    font-weight: 600 !important;
}
.filters-panel .gr-input-label { color: #333 !important; }

/* Slider accent */
input[type="range"] { accent-color: #ff6b00 !important; }

/* Radio / checkbox */
.gr-radio label, .gr-checkbox-group label {
    background: #fff !important;
    border: 1.5px solid #e8e8e8 !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    color: #333 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
    font-family: 'Inter', sans-serif !important;
}
.gr-radio label:hover, .gr-checkbox-group label:hover {
    border-color: #ff6b00 !important;
    background: #fff9f5 !important;
}
.gr-radio input:checked + label, .gr-checkbox-group input:checked + label {
    border-color: #ff6b00 !important;
    background: #fff5ee !important;
    color: #ff6b00 !important;
}

/* Submit button */
.cd-submit-btn {
    background: #ff6b00 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 12px 40px !important;
    color: #fff !important;
    box-shadow: 0 4px 16px rgba(255,107,0,0.3) !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}
.cd-submit-btn:hover {
    background: #e85d00 !important;
    box-shadow: 0 6px 20px rgba(255,107,0,0.4) !important;
}

/* Results */
#results-area { min-height: 100px; }
"""


# ──────────────────────────────────────────────────────────────
# Build compact Gradio UI
# ──────────────────────────────────────────────────────────────
with gr.Blocks(title="CarDekho - Find Your Perfect Car") as demo:

    # ── Header bar ────────────────────────────────────────────
    gr.HTML("""
    <div id="cd-header">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:24px;">&#128663;</span>
                <span style="color:#fff; font-size:22px; font-weight:800;
                             font-family:'Inter',sans-serif; letter-spacing:-0.3px;">
                    Car<span style="font-weight:400;">Dekho</span>
                </span>
            </div>
            <span style="color:rgba(255,255,255,0.85); font-size:13px;
                         font-family:'Inter',sans-serif;">
                Smart Car Recommendation
            </span>
        </div>
    </div>
    """)

    # ── All filters in one compact panel ──────────────────────
    with gr.Group(elem_classes=["filters-panel"]):

        gr.HTML("""
        <div style="margin-bottom:12px;">
            <span style="color:#222; font-size:16px; font-weight:700;
                         font-family:'Inter',sans-serif;">
                Tell us what you're looking for
            </span>
            <span style="color:#999; font-size:12px; font-family:'Inter',sans-serif;
                         margin-left:8px;">
                (just 3-4 quick inputs)
            </span>
        </div>
        """)

        # Row 1: Budget + Car Type
        with gr.Row():
            budget_slider = gr.Slider(
                minimum=3, maximum=25, value=10, step=0.5,
                label="Budget (Lakhs)",
                info="Max ex-showroom price",
                scale=2,
            )
            car_type_input = gr.Radio(
                choices=["Any", "SUV", "Sedan", "Hatchback"],
                value="Any",
                label="Car Type",
                scale=2,
            )

        # Row 2: Usage + Preferred Brand
        with gr.Row():
            usage_input = gr.Radio(
                choices=["City", "Highway", "Mixed"],
                value="Mixed",
                label="Primary Usage",
                scale=2,
            )
            brand_input = gr.CheckboxGroup(
                choices=BRAND_CHOICES,
                label="Preferred Brand (optional)",
                scale=2,
            )

    # ── Submit button (centered) ──────────────────────────────
    with gr.Row():
        gr.Column(scale=1)
        with gr.Column(scale=1):
            submit_btn = gr.Button(
                "Find Cars",
                variant="primary",
                elem_classes=["cd-submit-btn"],
            )
        gr.Column(scale=1)

    # ── Results area ──────────────────────────────────────────
    results_html = gr.HTML(
        value="""
        <div style="text-align:center; padding:30px 20px;">
            <div style="font-size:36px; margin-bottom:8px; opacity:0.5;">&#128269;</div>
            <p style="color:#999; font-family:'Inter',sans-serif; font-size:13px; margin:0;">
                Set your preferences and hit <strong style="color:#ff6b00;">Find Cars</strong>
            </p>
        </div>
        """,
        elem_id="results-area",
    )

    # ── Footer ────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center; padding:12px; margin-top:4px;">
        <p style="color:#bbb; font-size:11px; font-family:'Inter',sans-serif; margin:0;">
            CarDekho Recommendation Engine &middot; Gradio + FastAPI + SQLite
        </p>
    </div>
    """)

    # ── Wire up ───────────────────────────────────────────────
    submit_btn.click(
        fn=recommend_cars,
        inputs=[budget_slider, car_type_input, usage_input, brand_input],
        outputs=results_html,
    )


if __name__ == "__main__":
    demo.launch(css=CUSTOM_CSS, theme=gr.themes.Base())
