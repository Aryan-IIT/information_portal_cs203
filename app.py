import json
import os
import time
import logging
import json_log_formatter
from flask import Flask, render_template, request, redirect, url_for, flash
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import SpanKind, StatusCode

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
    
    # export to jaeger
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # export to console
    console_exporter = ConsoleSpanExporter()
    console_span_processor = BatchSpanProcessor(console_exporter)
    trace.get_tracer_provider().add_span_processor(console_span_processor)
    
    FlaskInstrumentor().instrument_app(app)
    LoggingInstrumentor().instrument()
    return tracer

tracer = setup_tracing()

def load_courses():
    """Load courses from the JSON file."""
    if not os.path.exists(COURSE_FILE):
        return []  # Return of list empty
    with open(COURSE_FILE, 'r') as file:
        return json.load(file)

def save_courses(data):
    """Save new course data to the JSON file."""
    courses = load_courses()  # Load courses
    courses.append(data)  # add course  
    with open(COURSE_FILE, 'w') as file:
        json.dump(courses, file, indent=4)

# Routes
@app.route('/')
def index():
    """Render the home page."""
    logger.info("Home page accessed.")
    return render_template('index.html')

@app.route('/catalog')
def course_catalog():
    """Display the course catalog page."""
    with tracer.start_as_current_span("render-course-catalog") as span:
        start_time = time.time()
        
        courses = load_courses()
        user_ip = request.remote_addr
        logger.info("Course catalog accessed.", extra={"total_courses": len(courses), "user_ip": user_ip})
        
        # Add trace attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.route", "/catalog")
        span.set_attribute("course.count", len(courses))
        span.set_attribute("user.ip", user_ip)
        
        response = render_template('course_catalog.html', courses=courses)
        processing_time = time.time() - start_time
        span.set_attribute("processing_time_ms", processing_time * 1000)
        
        return response

#1.1 Implementation, Feature of adding course
@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    """Handle adding a new course."""
    with tracer.start_as_current_span("add-course") as span:
        user_ip = request.remote_addr
        
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
                #1.2 feature, logging course addition 
                logger.info("Course added successfully.", extra={"course": course_data, "user_ip": user_ip})
                
                # Add trace attributes
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.route", "/add_course")
                span.add_event("Course saved to catalog.")
                span.set_attribute("user.ip", user_ip)
                
                flash(f"Course '{course_data['name']}' added successfully!", "success")
                return redirect(url_for('course_catalog'))
            
            except Exception as e:
                logger.error("Error adding course.", extra={"error": str(e), "user_ip": user_ip})
                span.record_exception(e)
                span.set_attribute("error", str(e))
                span.set_status(StatusCode.ERROR)  # Set span status to error
                flash("Failed to add the course. Please check the form inputs.", "error")
        
        return render_template('add_course.html')

@app.route('/course/<code>')
def course_details(code):
    """Display details for a specific course."""
    with tracer.start_as_current_span("course-details") as span:
        courses = load_courses()
        user_ip = request.remote_addr
        course = next((course for course in courses if course['code'] == code), None)
        
        if not course:
            logger.warning("Course not found.", extra={"course_code": code, "user_ip": user_ip})
            span.set_attribute("course.exists", False)
            span.set_attribute("user.ip", user_ip)
            span.set_status(StatusCode.ERROR)  # Set span status to error
            flash(f"No course found with code '{code}'.", "error")
            return redirect(url_for('course_catalog'))
        
        logger.info("Course details accessed.", extra={"course_code": code, "user_ip": user_ip})
        span.set_attribute("course.exists", True)
        span.set_attribute("course.code", code)
        span.set_attribute("user.ip", user_ip)
        return render_template('course_details.html', course=course)

@app.before_request
def track_requests():
    with tracer.start_as_current_span("request-tracker") as span:
        user_ip = request.remote_addr
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)
        span.set_attribute("user.ip", user_ip)
        span.add_event("New request tracked")

# Run the app.py
if __name__ == '__main__':
    logger.info("Starting the Flask application.")
    app.run(debug=True, host='0.0.0.0')
