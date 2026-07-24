export const capabilities = {
  erpnextExternalLinksEnabled: false,
} as const

export function isExternalErpNextAction(actionType?: string | null) {
  return Boolean(actionType && /open_erpnext|erpnext_external|open_erpnext_workflow/i.test(actionType))
}
