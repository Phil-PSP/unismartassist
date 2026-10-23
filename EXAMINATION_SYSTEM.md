# 📝 KAAF University Examination System

## Overview

A comprehensive online examination system that allows:
- **Students** to take online exams and quizzes
- **Admins/Staff** to create exams, upload past questions
- **Automatic grading** for multiple choice questions
- **Past question papers** repository

## Features

### For Students
✅ Take online exams with timer
✅ Multiple choice, True/False, Short answer, Essay questions
✅ Auto-save answers
✅ Immediate results (if enabled)
✅ Review past attempts
✅ Download past question papers
✅ Multiple attempts (configurable)

### For Admin/Staff
✅ Create and manage exams
✅ Add questions with multiple options
✅ Set exam duration and availability
✅ Upload past question papers (PDF, images)
✅ Auto-grading for objective questions
✅ Manual grading for subjective questions
✅ View student performance analytics

## Database Models

### 1. **ExamCategory**
- Organize exams (Quiz, Mid-Semester, Final, etc.)

### 2. **Exam**
- Main exam configuration
- Fields: title, course, type, duration, marks, settings
- Supports: shuffling, time limits, multiple attempts

### 3. **Question**
- Individual questions in an exam
- Types: Multiple Choice, True/False, Short Answer, Essay
- Supports: images, marks allocation

### 4. **QuestionOption**
- Options for multiple choice questions
- Mark correct answer(s)

### 5. **ExamAttempt**
- Student's attempt at an exam
- Tracks: start time, submission, score, status

### 6. **Answer**
- Student's answer to a question
- Auto-grading for objective questions

### 7. **PastQuestionFile**
- Uploaded past question papers
- Supports: PDF, images, documents

## URLs

```
/exams/                                    - List all exams
/exams/<exam_id>/                          - Exam details
/exams/<exam_id>/start/                    - Start new attempt
/exams/attempt/<attempt_id>/               - Take exam
/exams/attempt/<attempt_id>/save/          - Save answer (AJAX)
/exams/attempt/<attempt_id>/submit/        - Submit exam
/exams/attempt/<attempt_id>/result/        - View results
/exams/past-questions/                     - List past questions
/exams/past-questions/<file_id>/download/  - Download file
/exams/past-questions/upload/              - Upload (admin)
```

## Admin Panel

Access via `/admin/` to:
1. Create exam categories
2. Create exams
3. Add questions and options
4. Upload past question papers
5. View student attempts
6. Grade subjective questions

## Quick Start

### 1. Create an Exam (Admin)
```
1. Go to /admin/
2. Click "Exams" → "Add Exam"
3. Fill in details:
   - Title, Course, Type
   - Duration, Marks
   - Start/End time
4. Add questions inline or separately
5. Publish when ready
```

### 2. Add Questions
```
1. In exam admin, click "Add another Question"
2. Enter question text
3. Select question type
4. Add options (for multiple choice)
5. Mark correct answer
6. Set marks
```

### 3. Upload Past Questions
```
1. Go to /exams/past-questions/upload/
2. Select course
3. Upload PDF/image file
4. Set academic year and semester
5. Submit
```

### 4. Take an Exam (Student)
```
1. Go to /exams/
2. Click on available exam
3. Click "Start Exam"
4. Answer questions
5. Submit before time expires
6. View results (if enabled)
```

## Exam Settings Explained

- **shuffle_questions**: Randomize question order
- **shuffle_options**: Randomize option order
- **show_results_immediately**: Show score after submission
- **allow_review**: Let students review answers
- **max_attempts**: Number of times student can attempt
- **duration_minutes**: Time limit for exam
- **pass_mark**: Minimum score to pass

## Auto-Grading

- **Multiple Choice**: Automatic
- **True/False**: Automatic
- **Short Answer**: Manual (by staff)
- **Essay**: Manual (by staff)

## Security Features

- ✅ Time limits enforced
- ✅ Auto-submit on timeout
- ✅ One attempt at a time
- ✅ Answer auto-save (no data loss)
- ✅ Course registration check
- ✅ Exam availability validation

## Future Enhancements

- [ ] Question bank/pool
- [ ] Random question selection
- [ ] Proctoring features
- [ ] Detailed analytics
- [ ] Export results to Excel
- [ ] Bulk question import
- [ ] Question difficulty analysis
- [ ] Plagiarism detection

## Database Schema

```
ExamCategory
├── Exam
│   ├── Question
│   │   └── QuestionOption
│   └── ExamAttempt
│       └── Answer
│
PastQuestionFile
```

## API Endpoints (Future)

Can be extended to include REST API for:
- Mobile app support
- Third-party integrations
- Analytics dashboards

## Support

For issues or questions:
- Contact IT Support: itsupport@kaafuni.edu.gh
- Check admin documentation
- Review this guide

---

**Built for KAAF University by Philip Qhophi Tetteh N. Gakpetor**
