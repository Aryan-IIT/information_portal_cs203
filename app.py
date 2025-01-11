import json
import os
import time
import logging
import json_log_formatter
from flask import Flask, render_template, request, redirect, url_for, flash
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import SpanKind

# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'

# Logging Setup
formatter = json_log_formatter.JSONFormatter()
json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

# OpenTelemetry Setup
def setup_tracing():
    """Configure OpenTelemetry tracing and Jaeger exporter."""
    resource = Resource.create({"service.name": "course-catalog-service"})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    FlaskInstrumentor().instrument_app(app)
    return tracer

tracer = setup_tracing()


# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'


# OpenTelemetry Setup
resource = Resource.create({"service.name": "course-catalog-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",  # Ensure Jaeger is accessible at this address
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
FlaskInstrumentor().instrument_app(app)


def load_courses():
    """
    Load courses from the JSON file.
    Returns:
        list: A list of courses (empty if the file doesn't exist).
    """
    if not os.path.exists(COURSE_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(COURSE_FILE, 'r') as file:
        return json.load(file)


def save_courses(data):
    """
    Save new course data to the JSON file.
    Args:
        data (dict): The new course data to be saved.
    """
    courses = load_courses()  # Load existing courses
    courses.append(data)  # Append the new course
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)


# Routes
@app.route('/')
def index():
    """
    Render the home page.
    """
    logger.info("Home page accessed.")
    return render_template('index.html')


@app.route('/catalog')
def course_catalog():
    """
    Display the course catalog page.
    """
    with tracer.start_as_current_span("render-course-catalog") as span:
        start_time = time.time()
        
        courses = load_courses()
        logger.info("Course catalog accessed.", extra={"total_courses": len(courses)})
        
        # Add trace attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.route", "/catalog")
        span.set_attribute("course.count", len(courses))
        
        response = render_template('course_catalog.html', courses=courses)
        processing_time = time.time() - start_time
        span.set_attribute("processing_time_ms", processing_time * 1000)
        
        return response

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    """
    Handle adding a new course.
    """
    with tracer.start_as_current_span("add-course") as span:
        if request.method == 'POST':
            try:
                # Extract form data
                course_data = {
                    "code": request.form['code'],
                    "name": request.form['name'],
                    "instructor": request.form['instructor'],
                    "semester": request.form['semester'],
                    "schedule": request.form['schedule'],
                    "classroom": request.form['classroom'],
                    "prerequisites": request.form.get('prerequisites', 'None'),
                    "grading": request.form['grading'],
                    "description": request.form['description']
                }
                
                
                save_courses(course_data)
                logger.info("Course added successfully.", extra={"course": course_data})
                
                # Add trace attributes
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.route", "/add_course")
                span.add_event("Course saved to catalog.")
                
                flash(f"Course '{course_data['name']}' added successfully!", "success")
                return redirect(url_for('course_catalog'))
            
            except Exception as e:
                logger.error("Error adding course.", extra={"error": str(e)})
                span.record_exception(e)
                flash("Failed to add the course. Please check the form inputs.", "error")
        
        return render_template('add_course.html')


@app.route('/course/<code>')
def course_details(code):
    """
    Display details for a specific course.
    Args:
        code (str): The course code.
    """
    with tracer.start_as_current_span("course-details") as span:
        courses = load_courses()
        course = next((course for course in courses if course['code'] == code), None)
        
        if not course:
            logger.warning("Course not found.", extra={"course_code": code})
            span.set_attribute("course.exists", False)
            flash(f"No course found with code '{code}'.", "error")
            return redirect(url_for('course_catalog'))
        
        logger.info("Course details accessed.", extra={"course_code": code})
        span.set_attribute("course.exists", True)
        span.set_attribute("course.code", code)
        return render_template('course_details.html', course=course)


@app.route("/manual-trace")
def manual_trace():
    """
    Record a manual trace for custom operations.
    """
    with tracer.start_as_current_span("manual-span", kind=SpanKind.SERVER) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.add_event("Processing manual trace request.")
        logger.info("Manual trace recorded.")
        return "Manual trace recorded!", 200

@app.route("/auto-instrumented")
def auto_instrumented():
    """
    Demonstrate auto-instrumentation via FlaskInstrumentor.
    """
    logger.info("Auto-instrumented route accessed.")
    return "This route is auto-instrumented!", 200

@app.before_request
def track_requests():
    with tracer.start_as_current_span("request-tracker") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.add_event("New request tracked")

if __name__ == '__main__':
    logger.info("Starting the Flask application.")
    app.run(debug=True, host='0.0.0.0')


