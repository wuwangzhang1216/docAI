import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Add providers here as needed (e.g., theme, i18n, etc.)
function AllTheProviders({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return {
    user: userEvent.setup(),
    ...render(ui, { wrapper: AllTheProviders, ...options }),
  }
}

export * from '@testing-library/react'
export { customRender as render }
