# Epic E003: Creative Brief Chat Interface

## Overview
Implement ChatGPT-style conversational interface guided by Master Orchestrator Agent to collect brand info, product details, visual assets, and creative direction from users.

## Business Value
- Lowers barrier to entry (no complex forms)
- Natural, intuitive user experience
- Guides users through optimal workflow
- Prevents incomplete or invalid requests
- Enables AI to understand creative intent

## Success Criteria
- [ ] Chat interface displays messages chronologically
- [ ] Orchestrator guides through 5 stages (brand → product → assets → scenes → review)
- [ ] Users cannot skip required information
- [ ] Unsafe/inappropriate requests blocked with alternatives
- [ ] Chat history persists during session
- [ ] Visual stage indicator shows progress
- [ ] Support for text input and file uploads in chat

## Dependencies
- User authentication (E001)
- Project management (E002)
- Claude API integration
- WebSocket or polling for real-time updates

## Priority
**P0 - MVP Critical**

## Estimated Effort
**6-8 days** (2 frontend + 1 backend)

## Related Stories
- S013: Chat UI Component Architecture
- S014: Master Orchestrator Agent Implementation
- S015: Stage-Based State Machine
- S016: File Upload in Chat
- S017: Safety Content Filtering
- S018: Chat History Persistence
- S019: Stage Progress Indicator

## Orchestrator Stages
1. **collect_brand_info**: Brand name, product type
2. **collect_product_info**: Description, audience, benefit
3. **collect_assets**: Upload 2-4 product images
4. **collect_scenes**: Creative direction, scene preferences
5. **final_review**: Confirm details before generation
6. **generate_video**: Trigger pipeline
7. **export_video**: Download/publish options

## Technical Notes
- Use Zustand store for chat state management
- Implement optimistic UI updates
- Support markdown rendering in messages
- Add typing indicators
- Stream Claude responses for better UX
- Validate stage transitions server-side

## Example Flow
```
System: "👋 Hi! I'm your Zapcut assistant. What's your brand name?"
User: "Luna Coffee"
System: "Great! Tell me about your product."
User: "Organic cold brew concentrate"
System: "Perfect! Please upload 2-4 images of your product."
User: [uploads 2 images]
System: "Nice! Describe the visual style you want for your ad."
User: "Clean, modern, warm morning light"
System: "Got it! Here's a 5-scene storyboard. Ready to generate?"
User: "Yes!"
System: [starts generation]
```

## Security Considerations
- Validate all user inputs server-side
- Sanitize file uploads (scan for malware)
- Rate limit chat messages (10/minute)
- Block XSS attempts in markdown
- Implement profanity filter

## Success Metrics
- Chat completion rate: >75%
- Average time to generation: <5 minutes
- User abandonment rate: <20%
- Safety filter accuracy: >95%

---
**Created**: 2025-11-15  
**Status**: Draft  
**Owner**: Frontend + Backend Team
