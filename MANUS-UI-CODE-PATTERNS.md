# MANUS UI - Reusable Code Patterns

## 1. Button Variants

### Expandable Text Button (Primary)
```html
<button class="flex items-center text-[var(--text-primary)] rounded-[8px] 
  clickable font-medium border border-[var(--border-btn-main)] 
  overflow-hidden h-[32px] transition-[width,background-color,color,padding,gap] 
  duration-100 ease-out px-[12px] gap-[6px] bg-[var(--fill-white)] justify-center">
  <svg class="lucide lucide-monitor-play shrink-0" width="16" height="16">...</svg>
  <span class="text-[14px] tracking-[-0.091px] whitespace-nowrap font-medium 
    transition-opacity duration-100 ease-out opacity-100">Preview</span>
</button>
```

**Pattern Details:**
- Width animates from full to icon-only (32px)
- Text opacity transitions independently
- Gap collapses when collapsed
- Background changes on hover and active states

---

### Icon-Only Collapsed Button
```html
<button class="flex items-center text-[var(--text-primary)] rounded-[8px] 
  clickable font-medium border border-[var(--border-btn-main)] 
  overflow-hidden h-[32px] transition-[width,background-color,color,padding,gap] 
  duration-100 ease-out w-[32px] gap-0 bg-transparent 
  hover:bg-[var(--fill-tsp-white-light)] justify-center">
  <svg class="lucide lucide-code shrink-0" width="16" height="16">...</svg>
  <span aria-hidden="true" class="text-[14px] tracking-[-0.091px] 
    whitespace-nowrap font-medium transition-opacity duration-100 
    ease-out hidden opacity-0">Code</span>
</button>
```

**Pattern Details:**
- Fixed 32px square shape
- No padding or gap
- Transparent background (no outline default)
- Hidden text label (accessible but invisible)

---

### Dark Primary Button
```html
<button class="inline-flex items-center justify-center whitespace-nowrap 
  font-medium transition-colors hover:opacity-90 active:opacity-80 
  bg-[var(--Button-primary-black)] text-[var(--text-onblack)] gap-[6px] 
  text-sm rounded-full p-0 w-8 h-8 min-w-0">
  <svg width="15" height="15">...</svg>
</button>
```

**Pattern Details:**
- Pill shape (rounded-full)
- Fixed 8x8 size
- Opacity feedback (hover 90%, active 80%)
- White/light text on dark background

---

### Disabled Button State
```html
<button class="inline-flex items-center justify-center whitespace-nowrap 
  font-medium transition-colors hover:opacity-90 active:opacity-80 
  bg-[var(--Button-primary-black)] text-[var(--text-onblack)] gap-[6px] 
  text-sm rounded-full p-0 w-8 h-8 min-w-0 
  disabled:bg-[var(--fill-tsp-white-dark)] disabled:opacity-100 
  disabled:hover:opacity-100 disabled:active:opacity-100">
  <svg width="15" height="15">...</svg>
</button>
```

**Pattern Details:**
- Different background color when disabled
- Opacity stays 100% (not faded)
- Hover and active states disabled
- Maintains visual presence

---

## 2. Layout Patterns

### Sticky Header with Model Selector
```html
<div class="flex pt-3 pb-1 gap-1 ps-[16px] pe-[24px] sticky top-0 z-10 
  flex-shrink-0 bg-[var(--background-gray-main)]">
  <div class="flex items-center pointer-events-auto">
    <div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
      <div class="flex h-8 pt-[7px] pr-1.5 pb-[7px] pl-2 justify-center 
        items-center gap-1 rounded-[8px] clickable 
        hover:bg-[var(--fill-tsp-white-main)]" aria-expanded="false" 
        aria-haspopup="dialog">
        <span class="text-[var(--text-primary)] text-base font-[500] 
          leading-[22px]">Manus 1.5 Lite</span>
        <svg class="rotate-[90deg]">...</svg>
      </div>
    </div>
  </div>
</div>
```

**Pattern Details:**
- `sticky top-0 z-10` - Stays at top of scrolling container
- `flex-shrink-0` - Doesn't shrink below content
- `flex-1 min-w-0` - Text container shrinks with overflow
- RTL-aware padding (`ps-` and `pe-`)

---

### Multi-Column Header Bar
```html
<div class="flex items-center justify-between pb-[10px] pt-[12px] px-0">
  <!-- Left: Button group -->
  <div class="flex items-center gap-[5px]">
    <!-- Expandable button, icon buttons -->
  </div>
  
  <!-- Divider -->
  <div class="w-0 h-[16px] border-e border-[var(--border-main)]"></div>
  
  <!-- Right: Metadata + actions -->
  <div class="flex items-center gap-[4px]">
    <!-- Info text, action buttons -->
  </div>
</div>
```

**Pattern Details:**
- Divider uses `w-0` to avoid affecting layout
- `border-e` for RTL support
- Symmetric padding and spacing
- Flexible gaps between sections

---

### Flex Row with Icon + Text
```html
<div class="flex flex-row items-center gap-[6px] flex-1 min-w-0">
  <span class="text-[var(--text-primary)] text-base font-[500] 
    leading-[22px]">Manus 1.5 Lite</span>
  <svg class="rotate-[90deg]" color="var(--text-tertiary)">...</svg>
</div>
```

**Pattern Details:**
- `flex-row items-center` - Horizontal, vertically centered
- `flex-1` - Takes available space
- `min-w-0` - Allows text to shrink and truncate
- `gap-[6px]` - Consistent icon-text spacing
- Icon gets subtle color (`--text-tertiary`)

---

### Scrollable Container with CustomBar
```html
<div data-simplebar="init" class="[&_.simplebar-scrollbar]:opacity-0 
  [&_.simplebar-scrollbar::before]:bg-[var(--text-disable)] 
  [&:hover_.simplebar-scrollbar]:opacity-100 
  [&:hover_.simplebar-scrollbar::before]:bg-[var(--text-tertiary)] 
  [&_.simplebar-scrollbar::before]:w-[var(--simplebar-scrollbar-width)] 
  [&_.simplebar-track.simplebar-vertical]:w-[calc(var(--simplebar-scrollbar-width)+2px)] 
  [&_.simplebar-track.simplebar-vertical]:mr-1 
  [&_.simplebar-content-wrapper]:flex [&_.simplebar-content-wrapper]:flex-col 
  [&_.simplebar-content-wrapper]:h-full [&_.simplebar-content]:flex 
  [&_.simplebar-content]:flex-1 flex flex-1 min-w-0 h-full 
  [&_.simplebar-content]:flex-row simplebar-scrollable-y"
  style="--simplebar-scrollbar-width: 6px;">
  <!-- Content -->
</div>
```

**Pattern Details:**
- SimpleBar child selectors in Tailwind syntax
- Scrollbar hidden by default (opacity-0)
- Shows on hover with color change
- Dynamic width via CSS variable
- RTL-aware margin

---

## 3. File Attachment Component

```html
<div class="flex items-center gap-2.5 w-full px-4 py-2">
  <svg class="lucide lucide-history text-[var(--icon-secondary)] 
    size-4 flex-shrink-0">...</svg>
  <div class="flex flex-col w-full gap-[2px] overflow-hidden">
    <div class="text-sm truncate text-[var(--text-primary)]">
      Draft email content and prepare mass email campaign
    </div>
    <div class="text-xs truncate text-[var(--text-tertiary)]">
      Last modified: 14:55
    </div>
  </div>
  <div class="flex items-center gap-2 flex-shrink-0">
    <button class="inline-flex items-center justify-center whitespace-nowrap 
      font-medium transition-colors hover:opacity-90 active:opacity-80 
      text-[var(--text-primary)] rounded-[8px] gap-[4px] text-[13px] 
      leading-[18px] px-[8px] h-[32px] border 
      border-[var(--border-btn-main)] bg-transparent clickable 
      hover:bg-[var(--fill-tsp-white-light)]">
      <svg class="lucide lucide-copy size-4">...</svg>
    </button>
    <button>...</button>
  </div>
</div>
```

**Pattern Details:**
- Icon + text + actions layout
- Two-line text with truncation
- Metadata in smaller, tertiary color
- Flex-shrink-0 on icon and button group
- Responsive button group collapses together

---

## 4. Interactive States

### Hover State Pattern
```html
<div class="flex items-center group gap-2 w-full">
  <!-- Content -->
  <button class="float-right transition text-[12px] text-[var(--text-tertiary)] 
    invisible group-hover:visible">Delete</button>
</div>
```

**Pattern Details:**
- `group` on parent element
- `group-hover:` prefix on children
- `invisible` to hide without taking space
- `float-right` for positioning

---

### Opacity Transitions
```html
<span class="text-[14px] tracking-[-0.091px] whitespace-nowrap font-medium 
  transition-opacity duration-100 ease-out opacity-100">Preview</span>
<span aria-hidden="true" class="text-[14px] tracking-[-0.091px] 
  whitespace-nowrap font-medium transition-opacity duration-100 
  ease-out hidden opacity-0">Code</span>
```

**Pattern Details:**
- Independent opacity transitions
- `hidden` class combines with opacity
- `aria-hidden` for accessibility

---

## 5. Loading Indicator

```html
<div class="absolute top-0 left-0 w-full h-[3px] z-[10] 
  overflow-hidden pointer-events-none">
  <div class="h-full bg-[var(--text-blue)] transition-all duration-300 ease-out" 
    style="width: 100%; opacity: 0; box-shadow: 0 0 10px var(--text-blue);">
  </div>
</div>
```

**Pattern Details:**
- Positioned absolutely at top
- Thin 3px height for subtlety
- Blue glow effect via box-shadow
- `pointer-events-none` doesn't interfere with clicks
- Inline style for dynamic width animation

---

## 6. Indicator Badge/Dot

```html
<i class="bg-[var(--Button-primary-brand)] border-[0.5px] 
  border-[var(--background-gray-main)] rounded-full size-[6px] 
  aspect-square absolute top-[5px] right-[5px]"></i>
```

**Pattern Details:**
- `<i>` tag for non-semantic icon/indicator
- `size-[6px]` for both width and height
- `aspect-square` ensures perfect circle
- `rounded-full` for circular shape
- Absolute positioning with top/right
- `border-[0.5px]` for subtle outline

---

## 7. Floating Action Button

```html
<div class="absolute bottom-[12px] right-[20px]">
  <button type="button" class="relative rounded-[999px] bg-[#1a1a19] 
    text-[#ffffff] text-[13px] font-[500] leading-[18px] flex 
    items-center justify-center h-[40px] group hover:opacity-80">
    <div class="flex items-center justify-center h-full gap-2 clickable 
      px-[12px]">
      <svg>...</svg>
      Code
    </div>
    <div class="absolute -top-[2.75px] -right-[2.75px] w-[9px] h-[9px] 
      bg-[var(--text-blue)] rounded-full border-[1.5px] 
      border-[var(--background-white-main)]"></div>
  </button>
  <div class="absolute -right-[4px] -top-[4px] opacity-0 
    group-hover:opacity-100 bg-[#fff] rounded-full p-[1px] 
    border border-[#85848144]">
    <svg>...</svg>
  </div>
</div>
```

**Pattern Details:**
- Absolute positioning with bottom/right
- Dark background (#1a1a19) with white text
- Indicator dot with blue background
- Hover button shows on group-hover
- Pill shape (rounded-full)
- Gap between icon and text

---

## 8. Preview Container with Gradient

```html
<div class="flex-1 min-h-0 bg-[var(--background-card-gray)] 
  relative rounded-b-[12px] border border-[var(--border-main)]">
  <div class="w-full h-full bg-gradient-to-br 
    from-[var(--background-gray-main)] to-[var(--background-card-gray)] 
    rounded-b-[12px] flex items-center justify-center">
    <div class="bg-[var(--background-white-main)] relative overflow-hidden 
      transition-all duration-300 ease-in-out w-full h-full rounded-b-xl">
      <div class="absolute inset-0 pointer-events-none rounded-[inherit] 
        z-10 transition-opacity duration-300 ease-in-out opacity-0"></div>
      <iframe src="..." class="w-full h-full"></iframe>
    </div>
  </div>
</div>
```

**Pattern Details:**
- `flex-1 min-h-0` - Fills container, allows scroll
- Gradient background before content
- Inner container with white background
- Overlay div for effects (currently hidden)
- `rounded-[inherit]` on overlay
- Full-width iframe

---

## 9. Text Truncation Pattern

```html
<div class="max-w-[100%] truncate text-[var(--text-secondary)]">
  File content with long name...
</div>
```

**Pattern Details:**
- `max-w-[100%]` - Ensure parent constraint respected
- `truncate` - Single-line with ellipsis
- Secondary color for less important text

---

## 10. Close Button (Hover Reveal)

```html
<div class="absolute -right-[4px] -top-[4px] opacity-0 
  group-hover:opacity-100 bg-[#fff] rounded-full p-[1px] 
  border border-[#85848144]">
  <svg class="lucide lucide-x size-[16px]"></svg>
</div>
```

**Pattern Details:**
- Hidden by default (opacity-0)
- Shows on parent group-hover
- Positioned absolutely in corner
- Circular background
- Subtle border color

---

## Animation Patterns Summary

| Effect | Classes | Duration | Easing |
|--------|---------|----------|--------|
| Button expand | `transition-[width,...]` | 100ms | ease-out |
| Text fade | `transition-opacity` | 100ms | ease-out |
| Container change | `transition-all` | 300ms | ease-in-out |
| Hover dim | `hover:opacity-80` | instant | - |
| Color change | `hover:bg-[...]` | varies | - |

---

## Accessibility Patterns

### Semantic Attributes
```html
<!-- Expandable control -->
<div aria-expanded="false" aria-haspopup="dialog">...</div>

<!-- Scrollable region -->
<div role="region" aria-label="scrollable content">...</div>

<!-- Keyboard navigation -->
<button tabindex="0">...</button>

<!-- Hidden from screen readers -->
<span aria-hidden="true">...</span>
```

---

## Notes for Implementation

1. **CSS Variables**: All colors use `var()` - ensure CSS file defines them
2. **Lucide Icons**: Import as SVG or component library
3. **SimpleBar**: Install via npm, initialize with `data-simplebar="init"`
4. **RTL Support**: Uses `ps-` (padding-start) and `pe-` (padding-end)
5. **Dark Theme**: Assumes dark background with light text
6. **Responsive**: Uses flexbox and min-width constraints, not media queries
