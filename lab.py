from flask import Flask, request, render_template_string, send_file
import pandas as pd
from datetime import datetime
from io import BytesIO
import plotly.express as px
import base64

app = Flask(__name__)

# Helper function to convert DataFrame to CSV in memory
def convert_df_to_csv(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

@app.route("/", methods=["GET", "POST"])
def index():
    chart_html = ""
    table_html = ""
    download_link = ""
    error_message = ""
    options = []
    start_date = ""
    end_date = ""

    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            error_message = "No file uploaded."
        else:
            try:
                df = pd.read_excel(file)
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                df['date'] = pd.to_datetime(df['date']).dt.date
                options = df['test_type'].unique().tolist()

                selected_test_type = request.form.get("test_type")
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")

                if selected_test_type:
                    df = df[df['test_type'] == selected_test_type]

                if start_date:
                    df = df[df['date'] >= datetime.strptime(start_date, "%Y-%m-%d").date()]
                if end_date:
                    df = df[df['date'] <= datetime.strptime(end_date, "%Y-%m-%d").date()]

                if not df.empty:
                    fig = px.line(df, x="date", y="value", title=f"{selected_test_type} over Time")
                    chart_html = fig.to_html(full_html=False)

                    table_html = df.to_html(classes="table table-striped", index=False)

                    csv_buffer = convert_df_to_csv(df)
                    b64 = base64.b64encode(csv_buffer.getvalue()).decode()
                    download_link = f'data:text/csv;base64,{b64}'

            except Exception as e:
                error_message = f"Error processing file: {e}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔬 Soil & Water App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="theme-color" content="#000000">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <meta name="apple-mobile-web-app-title" content="Lab Manager">
        <link rel="apple-touch-icon" sizes="180x180" href="/static/ios-img-180.png">
        <link rel="apple-touch-icon" sizes="152x152" href="/static/ios-img-152.png">
        <link rel="apple-touch-icon" sizes="120x120" href="/static/ios-img-120.png">
        <style>
            body { font-family: Arial; padding: 20px; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>🔬 Soil & Water App</h1>

        <form method="post" enctype="multipart/form-data">
            <label>Upload Excel File:</label>
            <input type="file" name="file" accept=".xlsx" required><br><br>

            <label>Select Test Type:</label>
            <select name="test_type">
                {% for opt in options %}
                    <option value="{{ opt }}">{{ opt }}</option>
                {% endfor %}
            </select><br><br>

            <label>Start Date:</label>
            <input type="date" name="start_date" value="{{ start_date }}"><br><br>

            <label>End Date:</label>
            <input type="date" name="end_date" value="{{ end_date }}"><br><br>

            <button type="submit">Submit</button>
        </form>

        {% if error_message %}
            <p class="error">{{ error_message }}</p>
        {% endif %}

        {% if chart_html %}
            <h3>Test Result Chart:</h3>
            {{ chart_html|safe }}
        {% endif %}

        {% if table_html %}
            <h3>Filtered Data Table:</h3>
            {{ table_html|safe }}
        {% endif %}

        {% if download_link %}
            <br><a href="{{ download_link }}" download="filtered_results.csv">📥 Download Filtered CSV</a>
        {% endif %}
    </body>
    </html>
    """, chart_html=chart_html, table_html=table_html, download_link=download_link,
           error_message=error_message, options=options, start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    app.run(debug=True)