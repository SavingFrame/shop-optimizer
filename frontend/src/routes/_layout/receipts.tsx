import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/receipts")({
  component: ReceiptsLayout,
})

function ReceiptsLayout() {
  return <Outlet />
}
