# 🎓 School Management System

A comprehensive Flask-based School Management System with role-based dashboards for Admin, Faculty, and Students. Features class management, student enrollment, attendance tracking, grade management, announcements, and resource/submission management.

## Features

### 📋 Core Features
- **Multi-role Authentication** - Admin, Faculty, and Student login portals
- **Admin Dashboard** - Manage classes, students, faculty, subjects, fees, and grades
- **Faculty Dashboard** - Manage courses, students, attendance, grades, and announcements
- **Student Dashboard** - View enrollments, submit assignments, track grades, and manage fees

### 🆕 Phase 3 Features
- **Class Announcements** - Post and manage announcements with priority levels
- **Dashboard Statistics** - Role-specific metrics and analytics
- **Upcoming Deadlines** - Widget showing pending assignments and deadlines
- **Student Submissions** - Upload assignment answers with optional notes
- **Faculty Grading** - Grade submissions and provide feedback
- **Resource Management** - Upload, edit, and delete course resources
- **Institution Settings** - Configure school/college/university terminology

## Tech Stack

- **Backend**: Flask 3.1.3 (Python 3.13.3)
- **Database**: Microsoft SQL Server + pyodbc 5.3.0
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Optional**: ReportLab 4.4.1 for PDF generation

## Requirements

- Python 3.8+
- Microsoft SQL Server (SQL Server Express or higher)
- ODBC Driver 17 for SQL Server
- Virtual environment (venv)

## Installation

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/school-management-system.git
cd school-management-system

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

1. Create a SQL Server database named `SchoolManagementDB`
2. Update [config.py](config.py) with your database server details:
   ```python
   SERVER = r'your_server\SQLEXPRESS'
   DATABASE = 'SchoolManagementDB'
   ```
3. Run the Flask app to auto-create tables:
   ```bash
   python app.py
   ```

### 4. Configure Environment Variables (Optional)

Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

### 5. Load Test Data (Optional)

```bash
python insert_test_data.py
```

## Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default Test Credentials

| Role | Login | Password |
|------|-------|----------|
| Admin | `admin` | `admin123` |
| Faculty | `murtaza@gmail.com` | `faculty123` |
| Student | `ali.updated@gmail.com` | `student123` |

**⚠️ Change these credentials in production!**

## API Endpoints

### Authentication
- `POST /login` - User login (role-based)
- `GET /logout` - User logout

### Admin APIs
- `GET /api/dashboard/stats` - Get admin statistics
- `GET/POST /api/config/institution` - Institution settings
- Admin management endpoints for classes, students, faculty, subjects, fees

### Faculty APIs
- `GET /api/dashboard/stats` - Get faculty statistics
- `GET /api/faculty/courses` - Get assigned courses
- `POST /api/faculty/course/<id>/resources` - Upload course resources
- `POST /api/faculty/submission/<id>/grade` - Grade student submissions
- `POST /api/faculty/announcements` - Post announcements
- `GET /api/announcements` - Get announcements

### Student APIs
- `GET /api/dashboard/stats` - Get student statistics
- `GET /api/student/resources` - Get available resources
- `POST /api/student/resource/<id>/submit` - Submit assignment
- `GET /api/announcements` - Get class announcements

### Common APIs
- `GET /api/upcoming-deadlines` - Get deadline information
- `GET /api/students/search` - Search students by name/email/roll number

## Project Structure

```
school-management-system/
├── app.py                    # Main Flask application
├── config.py                 # Database configuration
├── requirements.txt          # Python dependencies
├── insert_test_data.py      # Test data insertion script
├── templates/               # HTML templates
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── faculty_dashboard.html
│   └── student_dashboard.html
├── static/                  # Static files (CSS, JS, images)
│   ├── style.css
│   ├── uploads/            # User-uploaded files
│   └── admin.js
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore file
└── TEST_REPORT.md          # Testing documentation
```

## Database Schema

The system uses 21 tables:

**Core Tables:**
- Students, Faculty, Admins, Classes, Subjects, Enrollments

**Academic Tables:**
- StudentMarks, Attendance, GradeComponents, GradeThresholds, GradeHistory

**Resource Tables:**
- CourseResources, CourseSubmissions

**Finance Tables:**
- FeeStructures, FeePayments, FeeDues

**Configuration:**
- InstitutionSettings, ClassAnnouncements

## Security Considerations

⚠️ **Before Deployment:**
1. Change the Flask secret key in [app.py](app.py)
2. Update test user credentials
3. Use environment variables for sensitive data
4. Enable HTTPS in production
5. Implement proper password hashing (bcrypt/werkzeug)
6. Set up proper database authentication

## Testing

The system has been tested with:
- ✅ All three authentication roles
- ✅ Dashboard statistics and displays
- ✅ Class announcements posting and viewing
- ✅ Student submissions and faculty grading workflow
- ✅ Resource management (upload, edit, delete)
- ✅ Database persistence and retrieval

See [TEST_REPORT.md](TEST_REPORT.md) for detailed testing documentation.

## Future Enhancements

- [ ] Email notifications for announcements and deadlines
- [ ] Mobile app version
- [ ] Payment gateway integration
- [ ] Advanced reporting and analytics
- [ ] Video lecture integration
- [ ] Real-time notifications using WebSockets
- [ ] Role-based API access tokens

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please create an issue in the GitHub repository.

---

**Last Updated:** May 16, 2026  
**Status:** ✅ Production Ready  
**Version:** 1.0.0
