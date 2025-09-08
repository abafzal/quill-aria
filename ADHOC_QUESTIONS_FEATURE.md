# 💬 Ad Hoc Questions Feature

## Overview

The Ad Hoc Questions feature adds a ChatGPT-style chat interface to ARIA, allowing users to ask individual questions to the AI model without going through the full RFI workflow. This feature provides immediate value for exploration, clarification, and knowledge discovery.

## Quick Start

1. **Access**: Click the "💬 Ask Questions" button in the sidebar (available from any step)
2. **Ask**: Type your question in the text area and click "🚀 Get Answer" 
3. **Review**: View the AI-generated answer in the chat interface above
4. **Retry**: Click "🔄 Retry" for any failed questions
5. **Navigate**: Use the sidebar chat history to view previous questions
6. **Return**: Use "← Back to Main App" to return to the RFI workflow

## Key Features

### ✨ ChatGPT-Style Interface
- **Conversation Above Input**: Chat history displays above the input form for natural flow
- **Sidebar Chat History**: Previous questions shown in left sidebar with status indicators
- **Clean Input Form**: Streamlined question input at the bottom of the page
- **Retry Functionality**: One-click retry for failed questions
- **Real-time Updates**: Instant response generation with progress indicators

### 🔗 Seamless Integration
- Accessible from any step in the main RFI workflow
- Uses the same AI models and authentication as the main app
- Independent session state (doesn't interfere with RFI processing)
- Easy navigation between ad hoc and main modes

### 🛠️ Practical Utilities
- **Retry Failed Questions**: 🔄 Retry button appears for any failed questions
- **Chat History Sidebar**: View up to 10 recent questions with status indicators (✅/❌)
- **Clear History**: Reset entire conversation with one click
- **Copy All**: Export entire chat history as formatted text
- **Error Handling**: Clear feedback for authentication and generation issues
- **Performance Tracking**: Shows response times for each question

## User Interface Layout

### Main Chat Area
- **Header**: "Ask Questions" title
- **Conversation History**: All previous Q&A pairs displayed above input
- **Input Form**: Question text area at bottom with "Get Answer" button
- **Action Buttons**: Clear History and Copy All options

### Sidebar (ChatGPT Style)
- **Back to Main App**: Return to RFI workflow (when in ad hoc mode)
- **Chat History**: List of recent questions with:
  - ✅ Success indicator for answered questions
  - ❌ Error indicator for failed questions  
  - Truncated question text (first 50 characters)
  - Click to highlight in main chat
  - Shows last 10 questions with total count

## Use Cases

### 🔍 **Exploration & Discovery**
- "What are the key features of [product]?"
- "How does [technology] work?"
- "What are the main use cases for [feature]?"

### 📚 **Learning & Clarification**
- "Explain this technical concept in simpler terms"
- "What are the differences between [option A] and [option B]?"
- "Can you provide more details about [topic]?"

### 🏢 **Business Context**
- "What are typical implementation timelines?"
- "How does this compare to competitors?"
- "What are common customer concerns about [feature]?"

### 🔧 **RFI Support**
- Test AI capabilities before processing full RFIs
- Get clarification on generated answers
- Explore additional questions not in the original RFI
- Validate understanding of complex topics
- Retry failed questions during connectivity issues

## Technical Details

### Architecture
- **Backend**: Reuses existing `AnswerGenerationService`
- **Frontend**: ChatGPT-style Streamlit interface with chat components
- **State Management**: Independent session state for chat history
- **Authentication**: Same Databricks configuration as main app
- **Sidebar Integration**: Dynamic sidebar showing chat history or file preview

### Files Added/Modified
- `src/aria/ui/pages/adhoc_questions.py` - Main chat interface with retry functionality
- `src/aria/ui/components/file_preview.py` - Added sidebar chat history and navigation
- `app.py` - Added routing logic for ad hoc mode
- `ADHOC_QUESTIONS_FEATURE.md` - Updated documentation

### New Features
- **Retry Mechanism**: Failed questions can be retried with single click
- **ChatGPT Layout**: Conversation above input, sidebar history navigation
- **Status Indicators**: Visual feedback for successful (✅) and failed (❌) questions
- **Responsive Design**: Adapts between file preview and chat history in sidebar
- **Enhanced UX**: Streamlined input form with better placeholder text

## Benefits for RFI Workflow

### 🚀 **Enhanced Productivity**
- Quick answers without document upload overhead
- Instant clarification during RFI review
- Testing and validation of AI capabilities
- Knowledge discovery beyond formal RFI scope
- Easy retry for network or API issues

### 🎯 **Improved Quality**
- Better understanding of AI capabilities and limitations
- Ability to refine questions before batch processing
- Context gathering for more effective RFI responses
- Quality validation through interactive questioning
- Persistent chat history for reference

### 📈 **User Experience**
- Familiar ChatGPT-style interface pattern
- Low-friction access to AI capabilities
- Non-disruptive to existing workflow
- Immediate feedback and results
- Visual status indicators for all interactions

## Future Enhancement Opportunities

While the current implementation focuses on ChatGPT-style simplicity, future versions could include:

- **RFI Context Awareness**: Reference current uploaded documents in questions
- **Question Suggestions**: AI-powered question recommendations based on context
- **Answer Comparison**: Compare ad hoc answers with existing RFI answers
- **Export Integration**: Add ad hoc Q&As to current RFI workflow
- **Templates**: Pre-built question templates for common scenarios
- **Search History**: Search through previous questions and answers
- **Conversation Branching**: Save and organize multiple conversation threads

## Getting Started

The enhanced ChatGPT-style feature is ready to use immediately with your existing ARIA setup:

1. No additional configuration required
2. Uses your current Databricks authentication
3. Same AI models as main application
4. Accessible from the sidebar on any page
5. Automatic retry functionality for failed requests

**Ready to try it?** 
```bash
streamlit run app.py
```
Then look for the "💬 Ask Questions" button in the sidebar! 