# MANUS UI Component Analysis Report

## Executive Summary
Complete HTML dump from the MANUS deployment interface reveals a sophisticated, dark-theme AI development platform with advanced preview, code, and dashboard features. The UI employs Tailwind CSS utilities with custom CSS variables for a cohesive design system.

**Key Characteristics:**
- Framework: Tailwind CSS + custom CSS variable system
- Theme: Dark-first with gray backgrounds and white text
- Icons: Lucide Icons library
- Scrolling: SimpleBar (custom scrollbar implementation)
- Layout: Multi-panel flex-based design
- Interactivity: Extensive hover states and transitions

---

## 1. TYPOGRAPHY PATTERNS

### Font Sizes
```
- text-[11px]  - Micro labels, timestamps
- text-[12px]  - Secondary text, metadata
- text-[13px]  - Body text, buttons
- text-[14px]  - Tab labels, interface text
- text-sm      - Small captions (assumed 14px)
- text-base    - Large text (assumed 16px)
```

### Font Weights & Styles
```
font-medium        - Primary interface weight
font-[500]         - Custom medium weight
font-mono          - Code/monospace text
whitespace-nowrap  - Prevent text wrapping on buttons/labels
truncate          - Ellipsis overflow handling
```

### Line Heights
```
leading-[14px]    - Compact spacing (12px text)
leading-[16px]    - Standard spacing
leading-[18px]    - Relaxed spacing (13px text)
leading-[22px]    - Spacious (16px text)
```

### Tracking (Letter Spacing)
```
tracking-[-0.091px]  - Tighter, premium feel
```

---

## 2. SPACING SYSTEM

### Gap Patterns (PRIMARY FLEXBOX SPACING)
```
gap-0      - 35+ instances (0px)
gap-1      - 6 instances (4px)
gap-2      - 19 instances (8px)
gap-[4px]  - Custom micro spacing
gap-[5px]  - Custom tight spacing
gap-[6px]  - Custom tight spacing (icon + text)
```

### Padding Breakdown
```
p-0        - Reset padding (11 instances)
p-3        - 12px padding
p-4        - 16px padding
px-0       - Horizontal reset (7 instances)
px-1       - 4px horizontal
px-[12px]  - Custom 12px horizontal
px-[24px]  - Custom 24px horizontal
py-2       - 8px vertical (2 instances)
```

### Position-Specific Spacing
```
ps-[16px]  - Padding-start (left) for RTL support
pe-[24px]  - Padding-end (right) for RTL support
pt-0       - No top padding
pt-3       - 12px top padding
pb-[10px]  - Custom 10px bottom padding
pb-1       - 4px bottom padding
```

---

## 3. COLOR SYSTEM (CSS VARIABLES)

### Primary Semantic Colors
```
var(--text-primary)           63x - Main text color
var(--text-secondary)         15x - Secondary text
var(--text-tertiary)          34x - Subtle/disabled text
var(--text-disable)            1x - Disabled state
var(--text-blue)               3x - Accent/highlight blue
var(--text-onblack)            8x - Text on dark backgrounds
```

### Background Colors
```
var(--background-gray-main)    4x - Primary dark background
var(--background-white-main)   2x - White backgrounds
var(--background-card-gray)    2x - Card backgrounds
var(--background-menu-white)   1x - Menu backgrounds
```

### Fill/Interaction Colors
```
var(--fill-white)              7x - White fill
var(--fill-tsp-white-light)   39x - Light white (hover states)
var(--fill-tsp-white-main)     1x - Main white fill
var(--fill-tsp-white-dark)    10x - Darker white (disabled)
var(--fill-tsp-gray-main)     21x - Gray fills
var(--fill-tsp-gray-dark)     13x - Darker gray
```

### Icon Colors
```
var(--icon-primary)            7x - Primary icons
var(--icon-secondary)         16x - Secondary icons
var(--icon-tertiary)          36x - Tertiary/subtle icons
var(--icon-onblack)            8x - Icons on dark backgrounds
```

### Border Colors
```
var(--border-main)            10x - Primary borders
var(--border-btn-main)        46x - Button borders (most used)
var(--border-light)           13x - Light borders
```

### Button Colors
```
var(--Button-primary-brand)    1x - Brand primary button
var(--Button-primary-black)   16x - Black/dark primary button
```

### Utility Colors
```
var(--function-success)        1x - Success indication
var(--simplebar-scrollbar-width) - Dynamic scrollbar width (6px)
```

---

## 4. BORDERS & SHADOWS

### Border Radius Patterns
```
rounded-full      - 999px (perfect circle for pills/badges)
rounded-[12px]    - Card borders (most common)
rounded-[15px]    - Larger cards/containers
rounded-[999px]   - Pill buttons
rounded-b-[12px]  - Bottom border radius
rounded-b-xl      - Bottom border radius
rounded-[8px]     - Button/control borders (frequent)
rounded-md        - Medium radius on icons/buttons
rounded-[inherit] - Match parent
```

### Border Widths
```
border              - 1px (default)
border-[0.5px]      - Very subtle
border-[1.5px]      - Slightly thicker
border-e            - Border-end (right, RTL-aware)
```

### Box Shadows
```
box-shadow: 0 0 10px var(--text-blue)  - Blue glow (loading state)
No explicit drop-shadows in HTML
```

---

## 5. INTERACTIVE STATES

### Hover Effects
```
hover:bg-[var(--fill-tsp-white-light)]  - Most common (39 instances)
hover:bg-[var(--fill-tsp-white-dark)]   - Alternative hover
hover:bg-[var(--fill-tsp-gray-main)]    - Gray hover
hover:opacity-80                         - Fade on hover
hover:opacity-90                         - Slight fade (buttons)
```

### Active States
```
active:opacity-80    - Pressed button state
```

### Disabled States
```
disabled:bg-[var(--fill-tsp-white-dark)]
disabled:opacity-100
disabled:hover:opacity-100
disabled:active:opacity-100
```

### Opacity Changes
```
opacity-0      - Hidden
opacity-50     - Half transparent
opacity-80     - Slightly transparent
opacity-90     - Slightly visible
opacity-100    - Fully opaque
invisible      - Hidden but space-taking
group-hover:opacity-100  - Show on parent hover
group-hover:visible      - Visibility on group hover
```

---

## 6. TRANSITIONS & ANIMATIONS

### Transition Properties
```
transition-opacity           - Alpha changes
transition-all              - All properties
transition-[width,background-color,color,padding,gap]  - Specific list
transition-colors           - Color changes
```

### Duration Patterns
```
duration-100    - 100ms (quick)
duration-300    - 300ms (standard)
duration-500    - 500ms (slow - not shown but common)
```

### Easing Functions
```
ease-out        - Decelerate ending
ease-in-out     - Smooth both ways
```

### Timing Examples
```
transition-opacity duration-100 ease-out      - Text fades quickly
transition-all duration-300 ease-in-out       - All properties smooth
transition-[width,...] duration-100 ease-out  - Specific properties fast
```

---

## 7. LAYOUT PATTERNS

### Flexbox Structures

**Row Layout (Horizontal)**
```
flex flex-row items-center gap-[6px] flex-1 min-w-0
- Stretches to fill space (flex-1)
- Prevents overflow (min-w-0)
- Vertically centered items
```

**Column Layout (Vertical)**
```
flex flex-col h-full flex-1 flex-shrink-0 min-w-0
- Full height content
- Flex basis for sizing
- No shrinking
```

**Icon + Text Pattern**
```
flex flex-row items-center gap-[6px]
- Consistent spacing between icon and label
```

**Sticky Header**
```
flex pt-3 pb-1 gap-1 ps-[16px] pe-[24px]
sticky top-0 z-10 flex-shrink-0
bg-[var(--background-gray-main)]
- Stays at top during scroll
```

### Grid/Container Patterns
```
flex-1 min-h-0               - Fill available space with scroll
flex-1 min-w-[390px]         - Minimum width constraint
w-full h-full                - Fill parent completely
relative h-full min-w-0 flex - Flex container with constraints
```

### Width/Height Sizing
```
w-full          - 100% width
h-full          - 100% height
h-[28px]        - Custom heights
w-[32px]        - Square icon sizes
size-[28px]     - Width and height together (shorthand)
size-[6px]      - Tiny indicators
min-w-[390px]   - Minimum width
min-w-0         - Allow shrinking below content
```

---

## 8. SPECIAL FEATURES & COMPONENTS

### Multi-Panel Layout (Main Structure)
Three-section horizontal split with iframes:
```
1. LEFT PANEL (Chat/Context) - ~44% width - min-w-[390px]
2. MIDDLE PANEL (Preview) - ~56% width - min-width: 600px
3. CONTENT AREA (Same as middle) - Repeated panels
```

### Chat/Message Component
```
class="relative flex flex-col h-full flex-1 flex-shrink-0 min-w-0"
- Scrollable message container
- Uses SimpleBar for custom scrollbars
- Sticky header with model selector
```

### File Attachment Display
```
- File icon with name
- File size metadata (10 KB, 297.20 KB)
- File type label
- Copy/History action buttons
- Hover delete button
```

### History/Memory Display
```
- History icon + timestamp
- Message preview with truncation
- Copy button
- History replay button
- Compact spacing for list efficiency
```

### Preview Panel
```
- Toggle buttons: Preview | Code | Dashboard | Database | File Storage | Settings
- Width-aware button animation (buttons expand on click)
- Icon-only mode for less important actions
- Divider between button groups
```

### Deployment/Preview Area
```
- Gradient background (from-gray to card-gray)
- Rounded bottom corners (rounded-b-[12px])
- Border styling
- Animated loading bar (blue, 3px height)
- Embedded iframe (sandboxed)
- Code button with blue indicator dot
- Close button with hover visibility
```

### Button States

**Large Button (Preview)**
```
flex items-center ... px-[12px] gap-[6px] ... h-[32px]
width: 130.304688px (dynamic, expands on click)
bg-[var(--fill-white)]
transition-[width,background-color,color,padding,gap] duration-100 ease-out
```

**Icon-Only Button (Collapsed)**
```
width: 32px (square)
gap-0
bg-transparent
hover:bg-[var(--fill-tsp-white-light)]
```

**Dark Primary Button**
```
bg-[var(--Button-primary-black)]
text-[var(--text-onblack)]
rounded-full
hover:opacity-90
active:opacity-80
w-8 h-8 (fixed size)
```

### Indicator Dots/Badges
```
- Notification indicator: size-[6px], rounded-full, absolute positioning
- Blue accent: bg-[var(--text-blue)]
- Border: 1.5px white border
- Position: top-[5px] right-[5px] absolute
```

### SimpleBar Scrolling (Custom Implementation)
```
Complex selector for styling custom scrollbar:
[&_.simplebar-scrollbar]:opacity-0
[&_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)]
[&:hover_.simplebar-scrollbar]:opacity-100

Scrollbar width: 6px
Margin: 1px
Tracks vertical dimension
```

### Label/Badge Component
```
rounded-[15px] px-[10px] py-[3px]
border border-[var(--border-light)]
bg-[var(--fill-tsp-gray-main)]
inline-flex gap-[4px] items-center
hover:bg-[var(--fill-tsp-gray-dark)]
```

---

## 9. ICON SYSTEM

### Icon Library
Lucide Icons (16x16 or 20x20px)

### Common Icons
```
lucide-monitor-play      - Preview/play action
lucide-code              - Code view
lucide-chart-pie         - Analytics/dashboard
lucide-database          - Database view
lucide-settings          - Settings/configuration
lucide-file-search       - File search
lucide-star              - Favorite/star
lucide-history           - History/time
lucide-x                 - Close/dismiss
lucide-check             - Confirm/checkmark
lucide-copy              - Copy to clipboard
lucide-chevron-down      - Dropdown/collapse
```

### Icon Sizing
```
size-[16px]   - Standard small icons
size-[20px]   - Slightly larger icons
width="16" height="16"  - Explicit sizing
```

### Icon Colors
Inherited from parent text color or explicitly set via stroke/fill

---

## 10. ACCESSIBILITY FEATURES

### Semantic Attributes
```
aria-expanded="false"     - Button state (expanded/collapsed)
aria-haspopup="dialog"    - Opens dialog
aria-label="scrollable content"  - Scrollable region
role="region"             - Content region
tabindex="0"              - Keyboard navigable
```

### Visual Accessibility
```
Understandable hover states
Icon + text labels on important buttons
Sufficient contrast with CSS variables
Text truncation with ellipsis for overflow
```

---

## 11. KEY DESIGN TOKENS & RATIOS

### Size Ratios
```
Gap: 0, 1, 2, 4, 5, 6 (px-based)
Radius: 8, 12, 15, 999 (px)
Button height: 28, 32, 40 (px)
Icon size: 6, 9, 16, 20, 24 (px)
Padding: 0, 1, 3, 4, 10, 12, 16, 24 (px)
```

### Z-Index Strategy
```
z-10   - Sticky headers, top bars
z-[10] - Loading progress bar
Default - Regular content
```

---

## 12. CSS VARIABLE ORGANIZATION

The system uses a semantic naming convention:

```
--text-{level}           → Primary, Secondary, Tertiary, Disable, OnBlack
--icon-{level}           → Primary, Secondary, Tertiary, OnBlack
--fill-tsp-{color}-{level}  → TSP (Transparent?) White/Gray in Light/Main/Dark
--background-{type}      → Gray-Main, White-Main, Card-Gray, Menu-White
--border-{level}         → Main, Light, Btn-Main
--Button-primary-{type}  → Brand, Black
--function-{result}      → Success
```

---

## 13. RESPONSIVE CONSIDERATIONS

### Fixed Breakpoints Observed
```
min-w-[390px]    - Chat panel minimum width
min-width: 600px - Preview panel minimum width
width: 56.1%     - Inline width for preview panel
```

### Scaling Classes
```
flex-1           - Flexible growth
min-w-0          - Allow shrinking
overflow-hidden  - Contain overflow
h-full, w-full   - Fill containers
```

---

## CODE SNIPPET EXAMPLES

### Complete Button Pattern
```html
<button class="flex items-center text-[var(--text-primary)] rounded-[8px] 
  clickable font-medium border border-[var(--border-btn-main)] 
  overflow-hidden h-[32px] transition-[width,background-color,color,padding,gap] 
  duration-100 ease-out px-[12px] gap-[6px] bg-[var(--fill-white)] 
  justify-center" style="width: 130.304688px;">
  <svg class="lucide lucide-monitor-play shrink-0">...</svg>
  <span class="text-[14px] tracking-[-0.091px] whitespace-nowrap font-medium 
    transition-opacity duration-100 ease-out opacity-100">Preview</span>
</button>
```

### Sticky Header Pattern
```html
<div class="flex pt-3 pb-1 gap-1 ps-[16px] pe-[24px] sticky top-0 z-10 
  flex-shrink-0 bg-[var(--background-gray-main)]">
  <!-- Content -->
</div>
```

### Flex Row with Icon + Text
```html
<div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
  <span class="text-[var(--text-primary)] text-base font-[500]">Manus 1.5 Lite</span>
  <svg class="rotate-[90deg]">...</svg>
</div>
```

### Indicator Badge
```html
<i class="bg-[var(--Button-primary-brand)] border-[0.5px] 
  border-[var(--background-gray-main)] rounded-full size-[6px] 
  aspect-square absolute top-[5px] right-[5px]"></i>
```

### Custom Scrollbar Styling
```html
<div data-simplebar="init" class="[&_.simplebar-scrollbar]:opacity-0 
  [&_.simplebar-scrollbar::before]:bg-[var(--text-disable)] 
  [&:hover_.simplebar-scrollbar]:opacity-100 
  [&:hover_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)] 
  [&_.simplebar-scrollbar::before]:w-[var(--simplebar-scrollbar-width)]
  ...">
</div>
```

### Preview Container with Gradient
```html
<div class="w-full h-full bg-gradient-to-br from-[var(--background-gray-main)] 
  to-[var(--background-card-gray)] rounded-b-[12px] flex items-center 
  justify-center">
  <div class="bg-[var(--background-white-main)] relative overflow-hidden 
    transition-all duration-300 ease-in-out w-full h-full rounded-b-xl">
    <iframe src="..." class="w-full h-full"></iframe>
    <!-- Floating code button -->
  </div>
</div>
```

---

## ENHANCEMENT OPPORTUNITIES

### Visual Polish
1. **Subtle shadows** on cards (currently absent)
2. **Blur backdrop** for overlays
3. **Micro-animations** on state changes
4. **Color transitions** during theme changes

### Spacing Improvements
1. More consistent gap patterns (currently 0, 1, 2, custom)
2. Consider establishing gap-3, gap-4 scales
3. Padding scale refinement

### Interactive Enhancements
1. More sophisticated hover states (scale, translate)
2. Skeleton loading states
3. Gesture feedback for touch devices

### Typography
1. Font size scale could be more granular
2. Consider line-height scale for different sizes
3. Font weight variation for visual hierarchy

---

## SUMMARY STATISTICS

- **Total unique CSS classes**: 80+
- **CSS variable usage**: 24 different semantic colors
- **Button variants**: 4 main types
- **Transition properties**: 6 different patterns
- **Layout types**: Flex-based (100%)
- **Icon library**: Lucide Icons (20+ icons)
- **File**: 162 lines of HTML
