---
name: Routinery Clone PRD
overview: Create a comprehensive Product Requirements Document outlining all features of a Routinery clone app for habit and routine management.
todos:
  - id: create-prd-file
    content: Write PRD document to scripts/prd.txt file in the project
    status: pending
---

# Routinery Clone - Product Requirements Document

Based on research of the Routinery app (routinery.app), its update notes, blog, and feature documentation, below is a comprehensive, tech-stack agnostic PRD.---

## 1. Product Overview

A habit and routine management application that helps users build, execute, and track daily routines through timer-guided workflows. The core philosophy is "Intention to Action" - helping users move forward without relying on willpower alone.**Target Users:**

- Individuals seeking to build consistent daily habits
- People with ADHD or executive function challenges
- Productivity-focused professionals
- Anyone wanting structure in their daily life

---

## 2. Core Features

### 2.1 Routine Creation & Management

| Feature | Description ||---------|-------------|| Custom Routines | Create routines with sequential tasks, each with configurable duration || Task Library | 800+ emojis/icons for visual task representation || Flexible Scheduling | Set routines for specific days (weekdays/weekends/custom) and times || Routine Categories | Morning, Evening, Productivity, Health, Relationships, Custom || Task Context | Add notes, links, motivational quotes, or background music to tasks || Routine Tags | Organize and filter routines with custom tags || Checklist Mode | Alternative mode for non-timed task completion |

### 2.2 Routine Execution

| Feature | Description ||---------|-------------|| Timer-Based Guidance | Visual countdown timer guiding through each task sequentially || Voice Alerts (TTS) | Text-to-speech announcements for task transitions || Push Notifications | Alerts for task changes and routine reminders || Flexible Controls | Pause, skip, adjust duration, or add tasks during execution || Multiple Timer Styles | Different visual timer presentations || Rest Mode | Pause routine execution for breaks || White Noise/Sounds | Background audio during routine execution |

### 2.3 Routine Triggers

| Feature | Description ||---------|-------------|| Time-Based | Start routines at scheduled times || Location-Based | Auto-trigger routines when arriving at specific locations (GPS) || Manual Start | Start routines on-demand || Alarm Integration | iOS alarm to wake and prompt routine start || Siri Shortcuts/Voice | Start routines via voice commands || Deep Links | Shareable links to start specific routines |

### 2.4 Progress Tracking & Analytics

| Feature | Description ||---------|-------------|| Daily/Weekly/Monthly Views | Performance summaries across time periods || Streak Tracking | Consecutive completion streaks with visual growth indicators || Task-Level Reports | Statistics on individual task completion || Calendar View | Historical view of routine completion || Journaling | Post-routine reflection and notes |

### 2.5 Gamification & Motivation

| Feature | Description ||---------|-------------|| Plant Badge System | Visual metaphor (seed → sprout → plant) representing streak growth || Achievement Badges | Rewards for milestones and consistency || Streak Saving | Mechanism to preserve streaks on missed days || Progress Widgets | Home screen widgets showing achievements |

### 2.6 Social & Community Features

| Feature | Description ||---------|-------------|| Friends System | Connect with other users || Progress Sharing | Share routine completion status with friends || Routine Sharing | Share routines via links for others to import || Explore Section | Browse community-created and curated routines || Famous Routines | Pre-built routines inspired by celebrities/experts |

### 2.7 Template Library

| Category | Examples ||----------|----------|| Morning Routines | Wake up, exercise, mindfulness, breakfast || Evening Routines | Wind down, skincare, reading, sleep prep || Productivity | Focus sessions, deep work, Pomodoro || Health & Wellness | Exercise, meditation, stretching || Famous Routines | Tim Ferriss, Oprah Winfrey, etc. |---

## 3. Platform Features

### 3.1 Cross-Device Support

- Mobile (iOS/Android)
- Tablet optimization
- Smartwatch (Apple Watch, Wear OS)
- Web application (optional)

### 3.2 Widgets

| Platform | Widget Types ||----------|--------------|| iOS | Routine progress, achievements, quick-start || Android | Routine progress, achievements, quick-start || Watch | Current task timer, routine shortcuts |

### 3.3 System Integrations

- Focus Mode / Do Not Disturb (iOS Screen Time)
- Calendar sync
- Siri Shortcuts / Google Assistant
- Notification customization
- Sticky notifications (Android persistent timer)

---

## 4. User Account & Data

### 4.1 Authentication

- Email/password registration
- Social login (Google, Apple, etc.)
- Password recovery
- Account deletion

### 4.2 Data Sync

- Real-time sync across devices
- Offline capability with sync on reconnect
- Data export functionality

### 4.3 Privacy & Security

- End-to-end data protection
- Clear privacy policies
- User consent for data sharing features
- GDPR/privacy regulation compliance

---

## 5. Monetization

### 5.1 Freemium Model

| Tier | Features ||------|----------|| Free | Basic routine creation, limited templates, ads || Premium | Unlimited routines, all templates, no ads, advanced analytics, cloud sync, widgets |

### 5.2 Subscription Management

- Monthly/yearly subscription options
- Family plans (optional)
- In-app purchase restoration
- Trial period

---

## 6. Accessibility

- ADHD-friendly design with structured visual guidance
- Voice prompts for hands-free operation
- Adjustable font sizes
- High contrast/dark mode
- Screen reader compatibility
- Multiple language support (localization)

---

## 7. Notifications System

| Type | Purpose ||------|---------|| Routine Reminders | Prompt to start scheduled routines || Task Transitions | Alert when moving to next task || Streak Reminders | Warning before losing a streak || Motivational | Encouragement and progress celebrations || Customization | User control over frequency and types |---

## 8. User Experience Principles

1. **Minimal Friction** - One-tap routine start, simple task progression
2. **Visual Clarity** - Clear timers, progress indicators, task icons
3. **Flexibility** - Adapt on-the-fly without breaking the flow
4. **Gentle Accountability** - Motivate without shame or pressure
5. **Progressive Disclosure** - Simple start, advanced features discoverable
6. **Focus on Execution** - Not just planning, but guided doing

---

## 9. Key Behavioral Features

Based on Routinery's behavioral science approach:

- **Habit Stacking** - Chain tasks to build momentum
- **Implementation Intentions** - Time/location triggers for "If-Then" planning
- **External Cues** - Audio/visual prompts to reduce reliance on memory
- **Reward Loops** - Streak visualization and badges for dopamine feedback
- **Friction Reduction** - Pre-planned sequences eliminate decision fatigue

---

## 10. Feature Priority Matrix