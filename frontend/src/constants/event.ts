/**
 * Re-exports UI panel event names from the typed eventBus.
 * Prefer importing from `@/utils/eventBus` for new code.
 */
export {
  UI_SHOW_FILE_PREVIEWER as EVENT_SHOW_FILE_PREVIEWER,
  UI_SHOW_COMPUTER_PANEL as EVENT_SHOW_COMPUTER_PANEL,
  UI_SHOW_FILE_PREVIEWER,
  UI_SHOW_COMPUTER_PANEL,
} from '../utils/eventBus'
