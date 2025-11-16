export const PRIMARY_SIDEBAR_LINKS = [
  {
    key: "brands",
    label: "Brands",
    path: "/dashboard",
    isActive: ({ pathname }) => pathname === "/dashboard" || pathname.startsWith("/brands"),
  },
  {
    key: "campaigns",
    label: "Campaigns",
    disabled: true,
    isActive: ({ pathname }) => pathname.startsWith("/campaigns"),
  },
  {
    key: "editor",
    label: "Editor",
    path: "/editor",
    isActive: ({ pathname }) => pathname.startsWith("/editor"),
  },
]

