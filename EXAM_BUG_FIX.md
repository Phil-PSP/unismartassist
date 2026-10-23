# 🐛 Bug Fix: Past Questions Page Error

## Issue
When accessing `/exams/past-questions/`, the following error occurred:

```
FieldError: Cannot resolve keyword 'registrations' into field.
Choices are: code, courseregistration, credit_hours, department, ...
```

## Root Cause
The `past_questions_list` view was using an incorrect field path to filter courses:

**Incorrect:**
```python
courses = Course.objects.filter(
    registrations__student_profile__user=request.user,
    registrations__is_active=True
)
```

**Problem:** 
- The `CourseRegistration` model has a ForeignKey to `Course` without a custom `related_name`
- Django automatically creates the reverse relation as `courseregistration_set` (not `registrations`)
- The `registrations` related name exists on `StudentProfile`, not on `Course`

## Solution
Fixed the field path to use the correct reverse relation:

**Correct:**
```python
try:
    student_profile = request.user.student_profile
    courses = Course.objects.filter(
        courseregistration__student=student_profile,
        courseregistration__is_active=True
    ).distinct()
except:
    courses = Course.objects.none()
```

## Model Relationships

### CourseRegistration Model:
```python
class CourseRegistration(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=CASCADE)  # No related_name!
    is_active = models.BooleanField(default=True)
```

### Correct Query Paths:

**From StudentProfile to Course:**
```python
# ✅ Correct
student_profile.registrations.filter(is_active=True)
```

**From Course to StudentProfile:**
```python
# ✅ Correct
Course.objects.filter(courseregistration__student=student_profile)

# ❌ Wrong
Course.objects.filter(registrations__student=student_profile)
```

## Files Modified
- `kaaf_chatbot/apps/exams/views.py` (line ~273)

## Status
✅ **FIXED** - Past questions page now loads correctly for students

## Testing
1. Login as student: `STU/2021/001` / `password123`
2. Navigate to: `/exams/past-questions/`
3. Page should load without errors
4. Shows courses the student is registered for

## Additional Improvements
- Added try-except block to handle users without student profiles
- Returns empty queryset if student profile doesn't exist
- Prevents crashes for admin/staff users accessing the page
