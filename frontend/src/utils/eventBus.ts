import mitt from 'mitt'

/** Keep string events for panel toggles; typed keys for project/session refresh */
export type AppEvents = {
  'projects:changed': undefined
  'sessions:changed': undefined
  [key: string]: unknown
}

export const eventBus = mitt<AppEvents>()