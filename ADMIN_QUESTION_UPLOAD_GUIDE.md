# Admin Guide: How to Upload Questions

## 📚 Overview

Admins can upload exam questions in **3 different ways**:

1. **Django Admin Panel** - Add questions one by one
2. **Bulk Upload (CSV)** - Upload multiple questions from Excel/CSV
3. **Bulk Upload (JSON)** - Upload structured question data
4. **AI Generation** - Let AI create questions automatically

---

## Method 1: Django Admin Panel (Manual Entry)

### Steps:
1. Login as admin: `ADM/001` / `admin123`
2. Go to: `http://127.0.0.1:8000/admin/`
3. Navigate to **"EXAMINATION SYSTEM"** → **"Exams"**
4. Click **"Add Exam"** or select an existing exam
5. Scroll down to **"Questions"** section
6. Click **"Add another Question"**
7. Fill in:
   - Question text
   - Question type (multiple choice, true/false, fill blank, etc.)
   - Marks
   - Order
8. For multiple choice questions, add options inline
9. Mark the correct answer(s)
10. Click **"Save"**

### Pros:
✅ Full control over each question
✅ Can add images to questions
✅ Easy to edit individual questions

### Cons:
❌ Time-consuming for many questions
❌ Manual data entry

---

## Method 2: Bulk Upload via CSV (Recommended for Excel Users)

### Steps:

#### 1. Download Template
- Go to: `http://127.0.0.1:8000/exams/questions/bulk-upload/`
- Click **"CSV Template"** to download
- Or direct link: `http://127.0.0.1:8000/exams/questions/template/csv/`

#### 2. Fill in Questions
Open the CSV file in Excel or Google Sheets and fill in your questions:

**Columns:**
- `question_text` - The question (required)
- `question_type` - Type: `multiple_choice`, `true_false`, `fill_blank`, `short_answer`, `essay`
- `marks` - Points (default: 1)
- `order` - Display order (default: 0)
- `options` - Options separated by `|` (e.g., "Paris|London|Berlin|Madrid")
- `correct_answers` - Index of correct option(s) (e.g., "0" for first option, "0,2" for multiple)
- `expected_answer` - For fill_blank questions only

**Example CSV:**
```csv
question_text,question_type,marks,order,options,correct_answers,expected_answer
"What is the capital of France?",multiple_choice,2,1,"London|Paris|Berlin|Madrid",1,
"Python is a programming language.",true_false,1,2,"True|False",0,
"The capital of France is _____.",fill_blank,1,3,,,Paris
"Explain object-oriented programming.",short_answer,5,4,,,
```

#### 3. Upload File
- Go to: `http://127.0.0.1:8000/exams/questions/bulk-upload/`
- Select the exam to add questions to
- Choose **"CSV"** format
- Upload your file
- Click **"Upload Questions"**

### Pros:
✅ Fast for many questions
✅ Works with Excel/Google Sheets
✅ Easy to edit in spreadsheet
✅ Can prepare offline

### Cons:
❌ Limited formatting options
❌ No image support

---

## Method 3: Bulk Upload via JSON (For Developers)

### Steps:

#### 1. Download Template
- Go to: `http://127.0.0.1:8000/exams/questions/bulk-upload/`
- Click **"JSON Template"** to download
- Or direct link: `http://127.0.0.1:8000/exams/questions/template/json/`

#### 2. Create JSON File
Create a JSON file with this structure:

```json
{
  "questions": [
    {
      "question_text": "What is the capital of France?",
      "question_type": "multiple_choice",
      "marks": 2,
      "order": 1,
      "options": [
        {"text": "London", "is_correct": false},
        {"text": "Paris", "is_correct": true},
        {"text": "Berlin", "is_correct": false},
        {"text": "Madrid", "is_correct": false}
      ]
    },
    {
      "question_text": "Python is a programming language.",
      "question_type": "true_false",
      "marks": 1,
      "order": 2,
      "options": [
        {"text": "True", "is_correct": true},
        {"text": "False", "is_correct": false}
      ]
    },
    {
      "question_text": "The capital of France is _____.",
      "question_type": "fill_blank",
      "marks": 1,
      "order": 3,
      "expected_answer": "Paris"
    }
  ]
}
```

#### 3. Upload File
- Go to: `http://127.0.0.1:8000/exams/questions/bulk-upload/`
- Select the exam
- Choose **"JSON"** format
- Upload your file
- Click **"Upload Questions"**

### Pros:
✅ Structured data format
✅ Easy to generate programmatically
✅ Version control friendly
✅ Can be validated before upload

### Cons:
❌ Requires JSON knowledge
❌ More complex than CSV

---

## Method 4: AI Generation (Fastest)

### Steps:
1. Go to: `http://127.0.0.1:8000/exams/ai/generate/`
2. Enter topic (e.g., "Python Programming")
3. Set number of questions (1-200)
4. Choose difficulty (easy/medium/hard)
5. Select question types
6. Click **"Generate Exam with AI"**

### Pros:
✅ Fastest method
✅ No manual question writing
✅ Generates complete exams instantly
✅ Supports up to 200 questions

### Cons:
❌ Less control over specific questions
❌ May need review/editing
❌ Requires AI API key

---

## Question Types Explained

### 1. Multiple Choice (`multiple_choice`)
- 4 options (A, B, C, D)
- Only 1 correct answer
- Auto-graded ✅

**CSV Example:**
```csv
"What is 2+2?",multiple_choice,1,1,"2|3|4|5",2,
```

**JSON Example:**
```json
{
  "question_text": "What is 2+2?",
  "question_type": "multiple_choice",
  "marks": 1,
  "options": [
    {"text": "2", "is_correct": false},
    {"text": "3", "is_correct": false},
    {"text": "4", "is_correct": true},
    {"text": "5", "is_correct": false}
  ]
}
```

### 2. True/False (`true_false`)
- 2 options (True/False)
- Auto-graded ✅

**CSV Example:**
```csv
"The Earth is flat.",true_false,1,1,"True|False",1,
```

### 3. Fill in the Blank (`fill_blank`)
- Text input field
- Case-insensitive matching
- Auto-graded ✅

**CSV Example:**
```csv
"The capital of France is _____.",fill_blank,1,1,,,Paris
```

**JSON Example:**
```json
{
  "question_text": "The capital of France is _____.",
  "question_type": "fill_blank",
  "marks": 1,
  "expected_answer": "Paris"
}
```

### 4. Short Answer (`short_answer`)
- Text area for answer
- Manual grading required ⚠️

**CSV Example:**
```csv
"Define photosynthesis.",short_answer,3,1,,,
```

### 5. Essay (`essay`)
- Large text area
- Manual grading required ⚠️

**CSV Example:**
```csv
"Discuss the causes of World War II.",essay,10,1,,,
```

---

## Tips & Best Practices

### CSV Tips:
1. **Use quotes** for text with commas: `"What is 2+2, exactly?"`
2. **Separate options with |**: `"Option A|Option B|Option C|Option D"`
3. **Index starts at 0**: First option is 0, second is 1, etc.
4. **Multiple correct answers**: Use commas: `"0,2"` for options 1 and 3
5. **Save as UTF-8** to preserve special characters

### JSON Tips:
1. **Validate JSON** before uploading (use jsonlint.com)
2. **Use proper quotes**: Double quotes `"` not single `'`
3. **Boolean values**: `true` and `false` (lowercase, no quotes)
4. **Arrays**: Use `[]` for lists
5. **Objects**: Use `{}` for structured data

### General Tips:
1. **Test with small batch first** (5-10 questions)
2. **Review uploaded questions** in admin panel
3. **Use consistent formatting** across questions
4. **Set appropriate marks** for difficulty
5. **Order questions logically** (use order field)
6. **Backup your data** before bulk operations

---

## Troubleshooting

### "File format not supported"
- Ensure file extension is `.csv` or `.json`
- Check file is not corrupted

### "Invalid CSV format"
- Check all required columns are present
- Ensure proper quoting of text fields
- Verify no extra commas or line breaks

### "Invalid JSON"
- Validate JSON syntax at jsonlint.com
- Check for missing commas or brackets
- Ensure proper quote usage

### "Question creation failed"
- Check question_type is valid
- Verify marks is a number
- Ensure options are provided for multiple_choice
- Check correct_answers indices are valid

### "No questions created"
- Verify exam was selected
- Check file is not empty
- Review error messages for specific issues

---

## Access URLs

- **Bulk Upload Page**: http://127.0.0.1:8000/exams/questions/bulk-upload/
- **CSV Template**: http://127.0.0.1:8000/exams/questions/template/csv/
- **JSON Template**: http://127.0.0.1:8000/exams/questions/template/json/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **AI Generator**: http://127.0.0.1:8000/exams/ai/generate/

---

## Quick Access

From the **Exam List** page, admins will see a **"Bulk Upload Questions"** button in the top right corner.

---

## Support

For issues or questions:
1. Check error messages carefully
2. Review this guide
3. Test with template files first
4. Check Django server logs for detailed errors

---

**Last Updated**: May 12, 2026
**Version**: 1.0
