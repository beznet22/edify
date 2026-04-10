import * as React from "react"

import { cn } from "@/lib/utils"

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60

  const mm = String(m).padStart(2, "0")
  const ss = String(s).padStart(2, "0")

  if (h >= 1) {
    const hh = String(h).padStart(2, "0")
    return `${hh}:${mm}:${ss}`
  }

  return `${mm}:${ss}`
}

function SessionTimer({
  className,
  seconds,
  ...props
}: Omit<React.ComponentProps<"span">, "children"> & {
  seconds: number
}) {
  return (
    <span
      data-slot="session-timer"
      className={cn(
        "inline-flex items-center rounded-full bg-muted/30 px-2.5 py-1 font-mono text-[0.6875rem] text-muted-foreground",
        className
      )}
      {...props}
    >
      SESSION TIME: {formatTime(seconds)}
    </span>
  )
}

export { SessionTimer }
