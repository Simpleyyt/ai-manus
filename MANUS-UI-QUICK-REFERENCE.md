# MANUS UI Quick Reference Guide

## Design System Overview

### Technology Stack
- **CSS Framework**: Tailwind CSS (arbitrary values enabled)
- **Icons**: Lucide Icons (SVG-based, colorable)
- **Scrolling**: SimpleBar (custom styled scrollbars)
- **Theming**: CSS Custom Properties (24 semantic colors)
- **Layout**: 100% Flexbox-based

---

## Color Palette Summary

### Text Hierarchy
```
Primary (63x)     → Main content text
Secondary (15x)   → Supporting text
Tertiary (34x)    → Hints, labels, disabled text
OnBlack (8x)      → Text over dark backgrounds
```

### Interactive Fills
```
Fill-White        → Main buttons, white fills
Fill-Light (39x)  → Hover states (most common)
Fill-Dark (10x)   → Disabled states
Fill-Gray (34x)   → Secondary fills, backgrounds
```

### Key Colors
```
Icon-Tertiary (36x)  → Most common icon color (subtle)
Border-Btn (46x)     → Button borders (most used)
Text-Blue (3x)       → Accent/loading indicator
```

---

## Component Patterns

### Buttons (4 Variants)

| Type | Usage | Key Classes |
|------|-------|-------------|
| **Expandable** | Primary actions | `flex items-center ... transition-[width,background-color,color,padding,gap] duration-100` |
| **Icon-Only** | Secondary actions | `w-[32px] gap-0 hover:bg-[var(--fill-tsp-white-light)]` |
| **Dark Primary** | Critical actions | `bg-[var(--Button-primary-black)] rounded-full w-8 h-8` |
| **Ghost** | Tertiary actions | `bg-transparent border` |

### Spacing Grid

| Use | Classes | Pixels |
|-----|---------|--------|
| Component gap | `gap-0` | 0px |
| Icon-text gap | `gap-[6px]` | 6px |
| Section gap | `gap-2` | 8px |
| Padding | `px-[12px]` | 12px |
| Padding large | `px-[24px]` | 24px |

### Border Radius
```
Small controls: rounded-[8px]
Cards: rounded-[12px]
Badges: rounded-[15px]
Buttons: rounded-full (999px)
```

---

## Animation Timings

### Quick Feedback (100ms)
```
transition-opacity duration-100 ease-out  // Text fade
transition-[width,...] duration-100       // Button expand
```

### Standard Transition (300ms)
```
transition-all duration-300 ease-in-out   // All properties
```

### Interactive States
```
hover:opacity-80                          // Dim on hover
active:opacity-80                         // Press effect
disabled:opacity-100                      // Keep visible when disabled
```

---

## Key Components Found

### ✅ Multi-Panel Layout
- Left: Chat/Context panel (min-w: 390px)
- Right: Preview panels (3x with iframe embeds)
- Flexible widths based on viewport

### ✅ Sticky Headers
- Model selector ("Manus 1.5 Lite")
- Tab bars (Preview, Code, Dashboard, etc.)
- z-10 stacking

### ✅ File Attachments
- File icon + name
- Size metadata
- Copy/History buttons
- Truncated file content preview

### ✅ Custom Scrollbars
- SimpleBar library
- Dynamic width (6px)
- Opacity animations on hover
- Semantic color variables

### ✅ Floating Action Buttons
- Code button with blue indicator dot
- Positioned bottom-right
- Dark background (#1a1a19)
- Hover visibility toggle

### ✅ Loading Indicator
- Blue progress bar (3px height)
- Positioned at top
- Box shadow glow effect
- Full width animation

### ⚠️ Missing (Deployment/Memory Cards)
- Specific "Memories" component structure not visible
- "DeploymentCard" mentioned in filename but HTML shows generic preview panels
- File likely represents only one UI state/section

---

## Responsive Strategy

### Minimum Widths (Breakpoints)
```
Chat panel:     min-w-[390px]
Preview panel:  min-width: 600px (inline style)
```

### Flexible Sizing
```
flex-1                    // Takes available space
min-w-0                   // Allow shrinking below content
overflow-hidden           // Contain overflow
```

### Panel Sizing
```
Left panel:   ~43% (390px ÷ 56.1% viewport)
Right panel:  ~56% (calculated from inline style)
```

---

## Icon System

### Common Icon Sizes
- `size-[16px]` - Standard small icons (most common)
- `size-[20px]` - Slightly larger
- `size-4` - Tiny indicators
- `size-[6px]` - Badges/dots

### Icon Colors
- Inherited from text color
- Explicit: `text-[var(--icon-secondary)]`
- Can be stroke or fill (SVG dependent)

### Icon Library
Lucide Icons - 20+ icons used:
```
monitor-play, code, chart-pie, database, settings
file-search, star, history, x, check, copy
chevron-down (rotated)
```

---

## Accessibility Highlights

### Attributes Used
```html
aria-expanded="false"         <!-- Button state -->
aria-haspopup="dialog"        <!-- Opens modal -->
aria-label="scrollable content"
role="region"
tabindex="0"
```

### Visual Accessibility
- Sufficient color contrast via variables
- Hover states clear and visible
- Text truncation with `truncate` class
- Disabled states clearly marked

---

## CSS Variable Usage

### Most Frequently Used (Top 10)
```
1. var(--text-primary)           63x
2. var(--border-btn-main)        46x
3. var(--fill-tsp-white-light)   39x
4. var(--icon-tertiary)          36x
5. var(--text-tertiary)          34x
6. var(--fill-tsp-gray-main)     21x
7. var(--icon-secondary)         16x
8. var(--text-secondary)         15x
9. var(--fill-tsp-gray-dark)     13x
10. var(--border-light)          13x
```

### Variable Organization
```
Color domains:
  --text-*          (6 variants)
  --icon-*          (4 variants)
  --fill-tsp-*      (6 variants)
  --background-*    (4 variants)
  --border-*        (3 variants)
  --Button-primary-* (2 variants)
```

---

## Enhancement Opportunities

### High Impact
1. **Box shadows** on cards (subtle, elevated look)
2. **Backdrop blur** on modal overlays
3. **Scale animations** on button hover
4. **Loading skeleton** states

### Medium Impact
1. **Gradient overlays** on image backgrounds
2. **Focus rings** for keyboard navigation (currently missing)
3. **Smooth scroll behavior**
4. **Touch-friendly hover states** (scale up instead of just color)

### Low Impact
1. **Additional button variants** (outline, ghost variations)
2. **More granular font sizes** (text-[13.5px])
3. **Monospace font fallback** for code blocks
4. **Animation delays** for staggered list items

---

## Code Pattern Examples

### Standard Button
```html
class="flex items-center px-[12px] gap-[6px] h-[32px] 
  border border-[var(--border-btn-main)] 
  hover:bg-[var(--fill-tsp-white-light)]
  transition-[width,background-color,color,padding,gap] duration-100"
```

### Icon + Text Row
```html
class="flex flex-row items-center gap-[6px] flex-1 min-w-0"
```

### Sticky Container
```html
class="sticky top-0 z-10 flex-shrink-0 
  bg-[var(--background-gray-main)]
  pt-3 pb-1 px-[16px]"
```

### Custom Scrollbar
```html
class="[&_.simplebar-scrollbar]:opacity-0
  [&:hover_.simplebar-scrollbar]:opacity-100
  [&_.simplebar-scrollbar::before]:w-[var(--simplebar-scrollbar-width)]"
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Lines | 162 |
| Unique CSS Classes | 80+ |
| CSS Variables | 24 semantic colors |
| Button Variants | 4 main types |
| Icon Count | 20+ |
| Panels in HTML | 3 preview panels |
| Transition Types | 6 different patterns |
| Z-Index Levels | 2 (z-10 and default) |

---

## Design Philosophy

### ✅ Consistent
- Semantic color naming
- Uniform spacing grid
- Predictable hover behaviors
- Reusable component patterns

### ✅ Accessible
- ARIA labels present
- Color not sole indicator
- Keyboard navigable
- Sufficient contrast ratios

### ✅ Performance-Focused
- CSS variable system (no theme switching DOM changes)
- Minimal animation duration (100-300ms)
- SimpleBar for efficient scrolling
- Flex-based responsive layout

### ⚠️ Areas for Improvement
- No explicit focus ring styles (keyboard nav)
- Limited animation variety (mostly opacity)
- Could use more shadow depth
- Box-shadow effects minimal

---

## File Structure Notes

This appears to be a **single UI state** dump, not the complete application:
- Focuses on preview/preview split layout
- Shows chat panel integration
- Displays file attachment handling
- Demonstrates multi-panel switching

**Missing from this dump:**
- Modal/dialog components
- Form inputs and validation states
- Table/data grid components
- Authentication flows
- Navigation menus
- Notification toasts/alerts
