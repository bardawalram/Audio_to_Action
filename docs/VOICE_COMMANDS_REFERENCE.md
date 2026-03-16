# 🎤 Voice Commands Reference Card

## Quick Command Examples

### ✅ Single Question Update
```
"Update question 3 to 8 marks"
"Set question 5 to 7 marks"
"Change question 1 to 4.5 marks"
```

### ✅ Batch Update - Parallel Lists (RECOMMENDED)
```
"Update marks for questions 1, 2, 3 as 4, 5, 6"
"Questions 1, 2, 3, 4 as 5, 6, 7, 8"
"Set questions 1, 2, 3 to 4, 5, 6"
```

### ✅ Batch Update - Traditional Format
```
"1 marks 3, 2 marks 5, 3 marks 7"
"Question 1 marks 4, question 2 marks 6"
```

### ✅ Batch Update - For-Give Format
```
"For 1 give 3, for 4 give 6, for 7 give 8"
"For question 1 give 3, for 2 give 5"
```

### ✅ Batch Update - Is Format
```
"Question 1 is 3, question 2 is 5, question 5 is 9"
```

---

## 🔥 NEW: Handles STT Quirks Automatically!

### Before (Would Fail) ❌
```
You say: "Update marks for questions 1, 2, 3"
Whisper: "update marks 4 questions 1 2 3"  ← "for" became "4"
Result:  ❌ Parse error
```

### After (Works Perfectly) ✅
```
You say: "Update marks for questions 1, 2, 3"
Whisper: "update marks 4 questions 1 2 3"
System:  Auto-normalizes → "update marks for questions..."
Result:  ✅ Parsed correctly!
```

---

## 📋 What Happens Behind the Scenes

1. **You speak naturally**
2. **Whisper may mess up homophones** ("for" → 4, "to" → 2)
3. **System auto-fixes it** using normalization
4. **You see the correct confirmation**
5. **Everything just works** ✨

---

## 🎯 Pro Tips

### Tip 1: Use Parallel Lists for Speed
Instead of saying each pair individually:
```
❌ "1 marks 3, 2 marks 4, 3 marks 5, 4 marks 6"  (slow)
✅ "questions 1, 2, 3, 4 as 3, 4, 5, 6"  (fast!)
```

### Tip 2: Speak Clearly, Don't Worry About Perfect Phrasing
The system handles:
- "to" vs "2"
- "for" vs "4"
- Missing commas
- Different word orders

Just speak naturally!

### Tip 3: Check the Confirmation Table
Always review the table before confirming - it shows:
- Old vs New marks
- All questions being updated
- Total change

---

## 🚫 What NOT to Do

### ❌ Don't mix batch formats
```
❌ "questions 1, 2 as 3, and 4 marks 5"  (mixing parallel + traditional)
✅ "questions 1, 2, 4 as 3, 4, 5"  (stick to one format)
```

### ❌ Don't mismatch list lengths
```
❌ "questions 1, 2, 3 as 4, 5"  (3 questions, 2 marks)
✅ "questions 1, 2, 3 as 4, 5, 6"  (equal lengths)
```

---

## 🆘 Troubleshooting

### "Intent not matched"
- Try simpler phrasing
- Use exact keywords: "update", "question", "marks"
- Speak a bit slower

### "Wrong numbers extracted"
- Check if you're on QuestionWisePage (for context)
- Ensure you're speaking clearly
- Look at backend logs to see what Whisper transcribed

### "Some questions missing"
- Check if list lengths match (for parallel lists)
- Try traditional format as fallback

---

## 📞 Need Help?

1. Check backend logs: Look for "Normalizing STT text" to see what was heard
2. Check the guide: `STT_NORMALIZATION_GUIDE.md`
3. Run tests: `pytest test_stt_normalization.py`

---

**Remember**: The system is designed to handle imperfect speech. Just speak naturally! 🎤✨
