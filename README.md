# information_portal_cs203

Parthiv Patel - 23110237   

Aryan Solanki - 23110049

This is a Flask-based web application designed for managing a course catalog. The app includes functionalities such as viewing the catalog, adding courses, and viewing course details. It also integrates OpenTelemetry for distributed tracing and logging, providing insights into the application's performance and behavior.

## Features

- **Home Page:** A simple landing page.
- **Course Catalog:** View the list of available courses.
- **Add Course:** Add new courses to the catalog through a form.
- **Course Details:** View detailed information about a specific course.
- **Distributed Tracing:** Integrated with OpenTelemetry and Jaeger for tracing application requests.
- **Structured Logging:** Logs application events and errors in JSON format for easy analysis.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/information-portal.git
   cd information-portal

2. **Install Dependencies:**
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt

3. **Run app:**
   Run the app with:
   ```bash
   python app.py

4. Access the Application:
  Open your web browser and navigate to http://localhost:5000 to access the app.

## OpenTelemetry (OTel) and Logging Overview

### OpenTelemetry (OTel)
OpenTelemetry (OTel) is an open-source observability framework that provides tools for collecting, processing, and exporting telemetry data such as traces, metrics, and logs. In this application, OTel is used to:

- **Trace Requests:** Capture and export detailed trace data for each request, helping to monitor application performance and diagnose issues.
- **Jaeger Integration:** Traces are sent to Jaeger, a popular open-source distributed tracing system, for visualization and analysis.

### Logging
Logging is used to capture important events and system behaviors, providing insights into the application's operation. In this app:

- **Structured Logging:** Logs are formatted in JSON, making them easy to parse and analyze.
- **Key Information:** Logs include details such as log levels, timestamps, messages, and additional context like user IP addresses and request details.
- **Error Reporting:** Logs capture errors and exceptions, which can help in diagnosing and resolving issues quickly.
