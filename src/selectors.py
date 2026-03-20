"""UI selector abstraction layer for Google Flow.

All CSS/text/aria selectors for Google Flow UI elements.
Update this file when Google changes the UI — never hardcode selectors elsewhere.

Discovery method:
- Selectors marked # VERIFIED were confirmed by live browser inspection
- Selectors marked # INFERRED are based on semantic analysis of page structure
- Selectors marked # NEEDS VERIFICATION could not be confirmed (page auth required)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Selector:
    """Container for multi-strategy UI selector.

    Provides CSS, text, and aria-label based selectors for resilient element location.
    """

    css: str
    text: Optional[str] = None
    aria: Optional[str] = None
    description: str = ""

    def __str__(self) -> str:
        return f"Selector(css={self.css!r}, text={self.text!r}, aria={self.aria!r})"

    def __repr__(self) -> str:
        return self.__str__()


class FlowSelectors:
    """All UI selectors for Google Flow (labs.google/flow).

    Usage:
        from src.selectors import FlowSelectors
        prompt_input = FlowSelectors.PROMPT_INPUT.css

    Selector strategies (in order of preference):
    1. css: Most specific, update when Google changes class names
    2. aria: Most stable, tied to accessibility attributes
    3. text: Resilient to layout changes, fragile to copy changes
    """

    # === Input Area ===
    PROMPT_INPUT = Selector(
        css="textarea[placeholder*='prompt'], textarea[aria-label*='prompt'], div[contenteditable='true'][role='textbox']",
        text=None,
        aria="prompt",
        description="Main text input area where user types the image generation prompt",
    )  # NEEDS VERIFICATION — page requires auth for editor view

    PROMPT_TEXTAREA = Selector(
        css="textarea[class*='prompt'], textarea[class*='input'], div.editor-input textarea",
        text=None,
        aria="Write a prompt",
        description="Text area element for prompt entry (alternative selector)",
    )  # INFERRED from typical GenAI UI patterns

    # === Action Buttons ===
    GENERATE_BUTTON = Selector(
        css="button[aria-label*='Generate'], button[data-testid*='generate'], button.generate-button, button:has-text('Generate')",
        text="Generate",
        aria="Generate",
        description="Button to trigger image generation (often has sparkle/arrow icon)",
    )  # NEEDS VERIFICATION

    CREATE_BUTTON = Selector(
        css="button[aria-label*='Create'], button:has-text('Create'), button[data-testid*='create']",
        text="Create",
        aria="Create",
        description="Create/Generate button on the main interface",
    )  # INFERRED

    # === Model and Settings Selection ===
    MODEL_SELECTOR = Selector(
        css="select[aria-label*='model'], button[aria-label*='model'], div[role='combobox'][aria-label*='model'], div[class*='model-selector']",
        text=None,
        aria="model",
        description="Dropdown/selector for AI model (e.g., Nano Banana, Imagen)",
    )  # NEEDS VERIFICATION

    SETTINGS_PANEL_TRIGGER = Selector(
        css="button[aria-label*='settings'], button[aria-label*='Settings'], button[aria-label*='more options'], button[data-testid*='settings']",
        text=None,
        aria="settings",
        description="Button/element to open settings panel (model, aspect ratio, count)",
    )  # NEEDS VERIFICATION

    ASPECT_RATIO_SELECTOR = Selector(
        css="select[aria-label*='aspect'], button[aria-label*='aspect ratio'], div[role='option'][data-value*=':'], div[class*='aspect-ratio']",
        text=None,
        aria="aspect ratio",
        description="Dropdown or button group for selecting image aspect ratio (1:1, 16:9, etc)",
    )  # NEEDS VERIFICATION

    IMAGE_COUNT_SELECTOR = Selector(
        css="input[type='number'][aria-label*='count'], select[aria-label*='count'], div[role='slider'][aria-label*='images'], div[class*='image-count']",
        text=None,
        aria="number of images",
        description="Input for how many images to generate (typically 1-4)",
    )  # NEEDS VERIFICATION

    # === Generated Results ===
    GENERATED_IMAGE_CONTAINER = Selector(
        css="div[class*='generated'], div[class*='results'], section[aria-label*='generated'], div[data-testid*='result'], div[class*='gallery']",
        text=None,
        aria="generated images",
        description="Container element holding all generated image results",
    )  # NEEDS VERIFICATION

    GENERATED_IMAGE_ITEM = Selector(
        css="div[class*='generated'] img, div[class*='result'] img, figure img[src*='blob'], figure img[src*='lh3.googleusercontent'], img[data-testid*='result-image']",
        text=None,
        aria=None,
        description="Individual generated image element (img tag within results)",
    )  # NEEDS VERIFICATION

    FIRST_GENERATED_IMAGE = Selector(
        css="div[class*='generated'] img:first-of-type, div[class*='result'] img:first-of-type, figure img[src*='blob']:first-of-type",
        text=None,
        aria=None,
        description="First generated image (used to detect generation completion)",
    )  # NEEDS VERIFICATION

    # === Download Options ===
    IMAGE_DOWNLOAD_BUTTON = Selector(
        css="button[aria-label*='Download'], button[aria-label*='download'], a[download], button:has-text('Download')",
        text="Download",
        aria="Download",
        description="Download button on individual generated image",
    )  # NEEDS VERIFICATION

    IMAGE_DOWNLOAD_MENU = Selector(
        css="button[aria-label*='More options'], button[aria-label*='more'], button.icon-button[data-testid*='menu'], button:has-text('Share')",
        text=None,
        aria="More options",
        description="Three-dots/kebab menu on image hover for additional options (download, share)",
    )  # NEEDS VERIFICATION

    # === Status and Progress ===
    LOADING_INDICATOR = Selector(
        css="div[role='progressbar'], div[aria-label*='loading'], div[class*='spinner'], div[class*='loading'], [data-testid*='progress']",
        text=None,
        aria="loading",
        description="Spinner or progress bar shown during image generation",
    )  # NEEDS VERIFICATION

    GENERATION_STATUS = Selector(
        css="div[aria-live='polite'], div[aria-live='assertive'], div[class*='status'], p[class*='status']",
        text=None,
        aria="status",
        description="Live region indicating generation status (processing, complete, error)",
    )  # INFERRED

    GENERATION_COMPLETE_SIGNAL = Selector(
        css="div[class*='generated'] img[src]:not([src='']), img[src*='blob'][src*=':']:not([src*='placeholder'])",
        text=None,
        aria=None,
        description="Signal that generation is done: first image has real src attribute",
    )  # INFERRED

    # === Error and Safety Dialogs ===
    CAPTCHA_OVERLAY = Selector(
        css="iframe[src*='recaptcha'], iframe[title*='reCAPTCHA'], div[class*='captcha'], #recaptcha, div[class*='recaptcha']",
        text=None,
        aria=None,
        description="CAPTCHA challenge overlay (reCAPTCHA or similar)",
    )  # INFERRED

    CONSENT_DIALOG = Selector(
        css="div[role='dialog'], mat-dialog-container, div[class*='consent'], div[class*='terms'], div[data-testid*='dialog']",
        text=None,
        aria="dialog",
        description="Consent/terms dialog shown on first visit or after policy updates",
    )  # INFERRED

    CONSENT_ACCEPT_BUTTON = Selector(
        css="button[aria-label*='Accept'], button[aria-label*='agree'], button[aria-label*='understand'], button:has-text('I understand')",
        text="I understand",
        aria="Accept",
        description="Button to dismiss consent/terms dialog",
    )  # INFERRED

    SAFETY_FILTER_WARNING = Selector(
        css="div[role='alert'][class*='error'], div[class*='safety'], div[class*='policy'], p[class*='error'], div[class*='violation']",
        text=None,
        aria="alert",
        description="Content policy rejection message when prompt violates safety guidelines",
    )  # INFERRED

    SAFETY_ERROR_MESSAGE = Selector(
        css="div[class*='error-message'], div[class*='error-text'], p:contains('policy'), p:contains('content'), span[class*='error']",
        text=None,
        aria="error",
        description="Text content of safety policy violation message",
    )  # INFERRED

    QUOTA_EXCEEDED_DIALOG = Selector(
        css="div[role='dialog'][class*='quota'], div[class*='limit'], div[class*='rate-limit'], div:has-text('quota')",
        text="quota",
        aria=None,
        description="Rate limit / quota exceeded message dialog",
    )  # INFERRED

    ERROR_MESSAGE = Selector(
        css="div[role='alert'], div[class*='error-message'], p[class*='error'], span[class*='error'], div[class*='error-container']",
        text=None,
        aria="alert",
        description="General error or warning message display",
    )  # INFERRED

    # === Navigation and Meta ===
    PAGE_TITLE = Selector(
        css="h1, h2[class*='title'], div[class*='page-title']",
        text="Flow",
        aria="Flow",
        description="Page title or heading",
    )  # INFERRED

    MAIN_CONTENT_AREA = Selector(
        css="main, div[role='main'], section[class*='editor'], div[class*='workspace']",
        text=None,
        aria=None,
        description="Primary content/editing area of the application",
    )  # INFERRED


def get_selector(name: str, strategy: str = "css") -> Optional[str]:
    """Retrieve a selector by name and strategy.

    Args:
        name: Selector name (e.g., 'PROMPT_INPUT')
        strategy: One of 'css', 'text', 'aria'

    Returns:
        Selector string or None if not found

    Raises:
        AttributeError: If selector name not found
        ValueError: If strategy not valid

    Examples:
        >>> get_selector('PROMPT_INPUT', 'css')
        "textarea[placeholder*='prompt'], ..."
        >>> get_selector('GENERATE_BUTTON', 'text')
        'Generate'
        >>> get_selector('GENERATE_BUTTON', 'aria')
        'Generate'
    """
    if strategy not in ("css", "text", "aria"):
        raise ValueError(f"Invalid strategy: {strategy}. Use 'css', 'text', or 'aria'")

    try:
        selector = getattr(FlowSelectors, name)
    except AttributeError:
        raise AttributeError(
            f"Selector not found: {name}. Check FlowSelectors class for available selectors."
        )

    if strategy == "css":
        return selector.css
    elif strategy == "text":
        return selector.text
    elif strategy == "aria":
        return selector.aria

    return None


def list_all_selectors() -> dict:
    """List all available selectors and their strategies.

    Returns:
        Dictionary mapping selector names to Selector objects

    Examples:
        >>> selectors = list_all_selectors()
        >>> len(selectors)
        26
        >>> 'PROMPT_INPUT' in selectors
        True
    """
    selectors = {}
    for attr_name in dir(FlowSelectors):
        if not attr_name.startswith("_"):
            attr = getattr(FlowSelectors, attr_name)
            if isinstance(attr, Selector):
                selectors[attr_name] = attr
    return selectors
