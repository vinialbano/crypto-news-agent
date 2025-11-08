"use client"

import { type PropsWithChildren } from "react"
import { ColorModeProvider } from "./color-mode"

export function CustomProvider(props: PropsWithChildren) {
  return (
    <ColorModeProvider defaultTheme="light">
      {props.children}
    </ColorModeProvider>
  )
}
