# 🤖 AI Exam Generator - Documentation

## Overview

The AI Exam Generator allows students to create custom exams on any topic using Google's Gemini AI. Students can specify the topic, difficulty, number of questions, and question types, and the AI will generate a complete exam in seconds.

---

## Features

### ✨ **AI-Powered Generation**
- Generate exams on **any topic** (programming, history, science, etc.)
- Powered by **Google Gemini 1.5 Flash**
- High-quality, academically rigorous questions
- Instant generation (typically 5-10 seconds)

### 🎯 **Customization Options**
- **Topic**: Any subject or concept
- **Number of Questions**: 1-50 questions
- **Difficulty**: Easy, Medium, or Hard
- **Duration**: 5-180 minutes
- **Question Types**: 
  - Multiple Choice (4 options)
  - True/False

### 📊 **Exam Features**
- Auto-grading for objective questions
- Instant results after submission
- Answer review
- Multiple attempts (up to 3)
- Countdown timer
- Auto-save answers

---

## How to Use

### **For Students:**

1. **Navigate to AI Exam Generator**
   - Click "AI Exam Generator" in the sidebar
   - Or go to: `/exams/ai/generate/`

2. **Fill in the Form**
   - **Topic**: Enter what you want to be tested on
     - Examples: "Python Functions", "World War II", "Calculus Derivatives"
   - **Course Code** (optional): e.g., CS101, MATH201
   - **Number of Questions**: Choose 1-50
   - **Difficulty**: Select Easy, Medium, or Hard
   - **Duration**: Set exam time in minutes
   - **Question Types**: Check Multiple Choice and/or True/False

3. **Generate Exam**
   - Click "Generate Exam with AI"
   - Wait 5-10 seconds for AI to create your exam
   - You'll be redirected to the exam details page

4. **Take the Exam**
   - Click "Start Exam"
   - Answer all questions within the time limit
   - Submit and view your results immediately

5. **View Your AI Exams**
   - Click "My AI Exams" to see all your generated exams
   - Retake exams up to 3 times

---

## Technical Details

### **Architecture**

```
User Request
    ↓
AI Exam Generator View (views.py)
    ↓
AIExamGenerator Class (ai_exam_generator.py)
    ↓
Google Gemini API
    ↓
Parse JSON Response
    ↓
Create Exam + Questions in Database
    ↓
Redirect to Exam Detail Page
```

### **AI Prompt Structure**

The system sends a structured prompt to Gemini AI:

```
You are an expert exam creator. Generate {num_questions} high-quality exam questions about: {topic}

REQUIREMENTS:
- Difficulty level: {difficulty}
- Question types: {types}
- Questions should be clear, unambiguous, and academically rigorous
- For multiple choice: provide 4 options with only ONE correct answer
- For true/false: provide a clear statement
- Ensure questions test understanding, not just memorization

OUTPUT FORMAT (JSON):
{
  "questions": [
    {
      "question_text": "What is...",
      "question_type": "multiple_choice",
      "marks": 2,
      "options": [
        {"text": "Option A", "is_correct": false},
        {"text": "Option B", "is_correct": true},
        ...
      ]
    }
  ]
}
```

### **Database Models**

AI-generated exams use the same models as regular exams:
- `Exam` - Main exam record
- `Question` - Individual questions
- `QuestionOption` - Answer options
- `ExamAttempt` - Student attempts
- `Answer` - Student answers

**Special Category**: All AI exams are tagged with the "AI Generated" category.

---

## API Configuration

### **Gemini API Setup**

The system uses the Gemini API key from `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

**Current Configuration:**
- Model: `gemini-1.5-flash`
- Temperature: `0.7` (balanced creativity)
- Max Output Tokens: `4096`
- Timeout: `30 seconds`

---

## File Structure

```
apps/exams/
├── ai_exam_generator.py          # AI generation logic
├── views.py                       # View functions
│   ├── ai_exam_generator()       # Generation form & handler
│   └── my_ai_exams()             # List user's AI exams
├── urls.py                        # URL routing
└── models.py                      # Database models

templates/exams/
├── ai_exam_generator.html         # Generation form
└── my_ai_exams.html              # List of AI exams
```

---

## Example Topics

### **Programming:**
- Python Data Structures
- Object-Oriented Programming in Java
- SQL Queries and Joins
- Web Development with HTML/CSS
- JavaScript ES6 Features
- React Hooks

### **Computer Science:**
- Database Normalization
- Computer Networks OSI Model
- Operating Systems Scheduling
- Data Structures and Algorithms
- Software Testing Methods

### **General:**
- World War II Events
- Calculus Derivatives
- Organic Chemistry Reactions
- Shakespeare's Plays
- Economics Supply and Demand

---

## Validation & Limits

### **Input Validation:**
- Topic: Required, non-empty string
- Questions: 1-50 (enforced)
- Duration: 5-180 minutes (enforced)
- At least one question type must be selected

### **AI Response Validation:**
- JSON parsing with error handling
- Markdown code block removal
- Fallback to empty array on parse failure

### **Error Handling:**
- API timeout: 30 seconds
- Invalid JSON: Error message to user
- Missing questions: Error message
- Network errors: Graceful failure

---

## URLs

### **AI Exam Generator:**
```
/exams/ai/generate/
```

### **My AI Exams:**
```
/exams/ai/my-exams/
```

### **Take AI Exam:**
```
/exams/<exam_id>/
/exams/<exam_id>/start/
/exams/attempt/<attempt_id>/
```

---

## Navigation

The AI Exam Generator is accessible from:
1. **Sidebar**: "AI Exam Generator" link (under Academic section)
2. **Exam List Page**: "Generate AI Exam" button
3. **My AI Exams Page**: "Generate New Exam" button

---

## Benefits

### **For Students:**
- ✅ Practice on any topic, anytime
- ✅ Customize difficulty to your level
- ✅ Instant feedback and results
- ✅ Unlimited exam generation
- ✅ No waiting for instructors

### **For Learning:**
- ✅ Self-paced learning
- ✅ Identify knowledge gaps
- ✅ Prepare for real exams
- ✅ Test understanding, not memorization
- ✅ Diverse question formats

---

## Future Enhancements

### **Planned Features:**
1. **More Question Types**
   - Short answer
   - Essay questions
   - Fill in the blanks
   - Matching questions

2. **Advanced Options**
   - Specify learning objectives
   - Include code snippets
   - Add images/diagrams
   - Multi-topic exams

3. **AI Improvements**
   - Difficulty calibration
   - Question quality scoring
   - Adaptive difficulty
   - Explanation generation

4. **Analytics**
   - Topic mastery tracking
   - Performance trends
   - Weak area identification
   - Study recommendations

---

## Troubleshooting

### **"Failed to generate exam"**
- Check internet connection
- Verify Gemini API key in `.env`
- Check API quota/limits
- Try a simpler topic

### **"Invalid JSON response"**
- AI response parsing failed
- Try regenerating with different parameters
- Check server logs for details

### **"No questions generated"**
- Topic may be too vague
- Try being more specific
- Reduce number of questions

### **Slow generation**
- Normal for large exams (30+ questions)
- Typical time: 5-10 seconds
- Max timeout: 30 seconds

---

## Security & Privacy

- ✅ User authentication required
- ✅ Exams tied to user account
- ✅ No sharing of personal data with AI
- ✅ API key stored securely in environment variables
- ✅ Rate limiting on generation (future)

---

## Testing

### **Quick Test:**
1. Login as student: `STU/2021/001` / `password123`
2. Go to: `/exams/ai/generate/`
3. Enter topic: "Python Functions"
4. Set: 5 questions, Medium difficulty, 15 minutes
5. Click "Generate Exam with AI"
6. Wait for generation
7. Take the exam!

---

## Status

✅ **FULLY OPERATIONAL**

- AI generation: Working
- Database integration: Complete
- UI/UX: Polished
- Navigation: Added
- Error handling: Implemented
- Documentation: Complete

**Ready for production use!** 🚀
