import { describe, expect, it } from 'vitest';
import { highlightLibraryPreview } from '../libraryHighlight';

describe('highlightLibraryPreview', () => {
  it('escapes html and colors python keywords', () => {
    const html = highlightLibraryPreview('class Student:\n    def __init__(self):\n        return "<ok>"', 'py');
    expect(html).toContain('&lt;ok&gt;');
    expect(html).toContain('tok-kw');
    expect(html).toContain('class');
    expect(html).toContain('def');
  });

  it('colors strings', () => {
    const html = highlightLibraryPreview('print("hi")', 'py');
    expect(html).toContain('tok-str');
    expect(html).toContain('"hi"');
  });
});
