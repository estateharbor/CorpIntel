{
  "brand": {
    "product_name": "CorpIntel India",
    "positioning": "Premium B2B SaaS for real-time Indian company intelligence (MMR focus) — Zaubacorp depth + Crunchbase discovery + Bloomberg terminal-grade density.",
    "design_personality": [
      "trustworthy / institutional",
      "fast / analytical",
      "data-dense but calm (Linear-like restraint)",
      "Indian fintech-grade (navy + saffron accents, not loud)",
      "terminal-inspired precision (crisp gridlines, compact tables)"
    ],
    "non_negotiables": [
      "Mobile-first at 375px",
      "Polished dark mode using Tailwind dark: class strategy (next-themes)",
      "Solid, theme-aware surfaces (no transparency causing dark-text-on-dark issues)",
      "All interactive + key informational elements MUST include data-testid (kebab-case)",
      "Do NOT change backend contracts"
    ]
  },

  "inspiration_fusion": {
    "layout_principles": {
      "primary": "Linear.app: calm density, strong hierarchy, minimal chrome",
      "secondary": "Bloomberg terminal: crisp grid, compact data modules, quick scanning",
      "data_discovery": "Crunchbase: entity cards, tags, similar entities, profile tabs"
    },
    "interaction_principles": [
      "Progressive disclosure: show KPIs + top charts first; deeper tables behind tabs/accordions",
      "Command-palette style search suggestions (shadcn Command)",
      "Filter chips for active filters; badges for status/counts",
      "Skeletons everywhere; empty states always include a next action"
    ]
  },

  "typography": {
    "fonts": {
      "heading": {
        "family": "Sora",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "All headings, KPI numbers labels, navigation section titles"
      },
      "body": {
        "family": "Inter",
        "fallback": "ui-sans-serif, system-ui",
        "usage": "Body, tables, forms, helper text"
      },
      "data_mono_optional": {
        "family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
        "usage": "CIN, numeric IDs, API keys, export codes (optional; do not overuse)"
      }
    },
    "tailwind_font_setup": {
      "note": "Main agent should add Google Fonts import for Inter + Sora in index.html or via CSS @import, then set Tailwind fontFamily in tailwind.config.js.",
      "recommended": {
        "font-sans": "Inter",
        "font-heading": "Sora"
      }
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-heading tracking-tight",
      "h2": "text-base md:text-lg text-muted-foreground",
      "section_title": "text-lg font-heading",
      "kpi_value": "text-2xl sm:text-3xl font-heading tabular-nums",
      "body": "text-sm sm:text-base",
      "small": "text-xs sm:text-sm"
    },
    "type_rules": [
      "Use tabular numbers for KPIs and tables: add `tabular-nums` on numeric cells.",
      "Keep line-height tight for headings (leading-[1.1]) and comfortable for body (leading-6).",
      "Avoid all-caps paragraphs; allow all-caps only for tiny labels (text-xs tracking-widest)."
    ]
  },

  "color_system": {
    "user_choices": {
      "primary_hex": "#1E3A5F",
      "accent_hex": "#F4A620",
      "background_hex": "#F8FAFC"
    },
    "token_strategy": {
      "note": "Map to shadcn CSS variables in HSL. Use navy as primary, saffron as accent. Keep surfaces solid and theme-aware.",
      "light": {
        "background": "210 40% 98%",
        "foreground": "215 28% 17%",
        "card": "0 0% 100%",
        "card-foreground": "215 28% 17%",
        "popover": "0 0% 100%",
        "popover-foreground": "215 28% 17%",

        "primary": "214 52% 25%",
        "primary-foreground": "210 40% 98%",

        "secondary": "210 30% 96%",
        "secondary-foreground": "214 52% 25%",

        "muted": "210 30% 96%",
        "muted-foreground": "215 16% 46%",

        "accent": "38 90% 54%",
        "accent-foreground": "214 60% 14%",

        "destructive": "0 72% 51%",
        "destructive-foreground": "210 40% 98%",

        "border": "214 20% 88%",
        "input": "214 20% 88%",
        "ring": "38 90% 54%",

        "radius": "0.75rem",

        "chart": {
          "chart-1": "214 52% 25%",
          "chart-2": "38 90% 54%",
          "chart-3": "199 78% 38%",
          "chart-4": "152 55% 36%",
          "chart-5": "0 72% 51%"
        },

        "semantic": {
          "success": "152 55% 36%",
          "warning": "38 90% 54%",
          "info": "199 78% 38%",
          "danger": "0 72% 51%",
          "status_active_bg": "152 55% 95%",
          "status_active_fg": "152 55% 26%",
          "status_struck_bg": "0 72% 95%",
          "status_struck_fg": "0 72% 40%",
          "status_liq_bg": "38 90% 94%",
          "status_liq_fg": "38 90% 34%"
        }
      },
      "dark": {
        "background": "214 55% 10%",
        "foreground": "210 40% 96%",
        "card": "214 50% 12%",
        "card-foreground": "210 40% 96%",
        "popover": "214 50% 12%",
        "popover-foreground": "210 40% 96%",

        "primary": "210 40% 96%",
        "primary-foreground": "214 60% 12%",

        "secondary": "214 35% 16%",
        "secondary-foreground": "210 40% 96%",

        "muted": "214 35% 16%",
        "muted-foreground": "215 18% 70%",

        "accent": "38 90% 54%",
        "accent-foreground": "214 60% 12%",

        "destructive": "0 62% 42%",
        "destructive-foreground": "210 40% 96%",

        "border": "214 28% 20%",
        "input": "214 28% 20%",
        "ring": "38 90% 54%",

        "radius": "0.75rem",

        "chart": {
          "chart-1": "210 40% 96%",
          "chart-2": "38 90% 54%",
          "chart-3": "199 78% 55%",
          "chart-4": "152 55% 50%",
          "chart-5": "0 62% 55%"
        },

        "semantic": {
          "success": "152 55% 50%",
          "warning": "38 90% 54%",
          "info": "199 78% 55%",
          "danger": "0 62% 55%",
          "status_active_bg": "152 55% 18%",
          "status_active_fg": "152 55% 70%",
          "status_struck_bg": "0 62% 18%",
          "status_struck_fg": "0 62% 72%",
          "status_liq_bg": "38 90% 18%",
          "status_liq_fg": "38 90% 70%"
        }
      }
    },
    "usage_rules": [
      "Primary navy is for navigation, headings, and primary buttons in light mode; in dark mode, primary becomes near-white for readability while navy becomes background/surfaces.",
      "Saffron is for CTAs, highlights, active states, and key chart series — keep it under ~10% of any viewport.",
      "Never use saturated dark gradients; if you use a gradient, keep it subtle and only as a hero background accent (<20% viewport).",
      "Status colors must be solid fills with readable foregrounds; never rely on color alone — include icon + label."
    ]
  },

  "design_tokens_css": {
    "where": "/app/frontend/src/index.css",
    "instructions": [
      "Replace the existing :root and .dark shadcn variables with the HSL values above.",
      "Add extra custom properties for app shell + data density (below) under :root and .dark.",
      "Do not add `.App { text-align:center }` anywhere."
    ],
    "additional_custom_properties": {
      "light": {
        "--surface-2": "210 30% 96%",
        "--surface-3": "214 25% 92%",
        "--sidebar": "214 52% 18%",
        "--sidebar-foreground": "210 40% 96%",
        "--sidebar-muted": "214 35% 22%",
        "--topbar": "0 0% 100%",
        "--topbar-foreground": "215 28% 17%",
        "--focus": "38 90% 54%",
        "--shadow-soft": "0 0% 0% / 0.06",
        "--shadow-med": "0 0% 0% / 0.10",
        "--gridline": "214 20% 88%",
        "--chip": "210 30% 96%",
        "--chip-foreground": "214 52% 25%"
      },
      "dark": {
        "--surface-2": "214 35% 16%",
        "--surface-3": "214 28% 20%",
        "--sidebar": "214 55% 9%",
        "--sidebar-foreground": "210 40% 96%",
        "--sidebar-muted": "214 35% 16%",
        "--topbar": "214 50% 12%",
        "--topbar-foreground": "210 40% 96%",
        "--focus": "38 90% 54%",
        "--shadow-soft": "0 0% 0% / 0.35",
        "--shadow-med": "0 0% 0% / 0.45",
        "--gridline": "214 28% 20%",
        "--chip": "214 35% 16%",
        "--chip-foreground": "210 40% 96%"
      }
    }
  },

  "layout_grid": {
    "app_shell": {
      "desktop": {
        "sidebar_width": "w-[272px]",
        "topbar_height": "h-14",
        "content_max_width": "max-w-[1400px] (center within content area only)",
        "content_padding": "px-4 sm:px-6 lg:px-8 py-6"
      },
      "mobile": {
        "pattern": "Topbar + Sheet (hamburger) for sidebar; quick search stays in topbar.",
        "content_padding": "px-4 py-4",
        "tables": "Use horizontal ScrollArea for wide tables; keep first column sticky when possible."
      }
    },
    "page_grids": {
      "dashboard": "12-col grid on lg; stack on mobile. KPI row: 2 cols mobile, 4 cols lg.",
      "search": "Sidebar filters collapse into Drawer on mobile; results are 1-col mobile, 2-col md, 3-col xl.",
      "company_detail": "Header + Tabs; within tabs use 12-col grid; similar companies: 2-col mobile, 3-col md, 6 cards.",
      "analytics": "Full-width charts stacked; add sticky subnav for city tabs on mobile.",
      "pricing": "1-col mobile, 2-col md, 4-col xl; Pro highlighted.",
      "settings": "Two-column on lg (nav list + content), stacked on mobile."
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui",
      "must_use": [
        "button.jsx",
        "input.jsx",
        "badge.jsx",
        "card.jsx",
        "tabs.jsx",
        "table.jsx",
        "pagination.jsx",
        "select.jsx",
        "slider.jsx",
        "switch.jsx",
        "dialog.jsx",
        "sheet.jsx",
        "drawer.jsx",
        "command.jsx",
        "popover.jsx",
        "calendar.jsx",
        "skeleton.jsx",
        "scroll-area.jsx",
        "progress.jsx",
        "sonner.jsx"
      ]
    },
    "component_styling_rules": {
      "buttons": {
        "shape": "Professional / Corporate: radius 10–12px (use --radius 0.75rem)",
        "primary": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-[hsl(var(--focus))]",
        "accent_cta": "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))] hover:brightness-[0.98]",
        "ghost": "bg-transparent hover:bg-muted",
        "motion": "transition-colors duration-150; active: scale-[0.98] (only on press)"
      },
      "inputs_search": {
        "search_bar": "Use Input + Command for suggestions. Add left icon (lucide Search).",
        "focus": "ring-2 ring-[hsl(var(--focus))] ring-offset-2 ring-offset-background",
        "density": "Use `h-10` for topbar search; `h-9` for filter sidebar inputs."
      },
      "badges_tags": {
        "status_badges": {
          "active": "bg-[hsl(var(--semantic-status_active_bg))] text-[hsl(var(--semantic-status_active_fg))]",
          "struck_off": "bg-[hsl(var(--semantic-status_struck_bg))] text-[hsl(var(--semantic-status_struck_fg))]",
          "under_liquidation": "bg-[hsl(var(--semantic-status_liq_bg))] text-[hsl(var(--semantic-status_liq_fg))]"
        },
        "city_tag": "Use Badge variant=secondary with subtle border; include MapPin icon.",
        "sector_chip": "Use Toggle/Badge-like chip; interactive chips must have hover + focus and data-testid."
      },
      "cards": {
        "kpi_card": "Card with compact padding p-4; top row label + delta; big number; tiny sparkline optional.",
        "company_card": "Card p-4; header row name + status; meta grid 2x2; chips row; footer actions (Track, Export) as ghost buttons.",
        "hover": "hover:shadow-[0_10px_30px_hsl(var(--shadow-soft))] hover:border-[hsl(var(--border))] transition-shadow transition-colors duration-150"
      },
      "tables": {
        "style": "Use shadcn Table; add zebra via `odd:bg-muted/40` (theme-safe).",
        "header": "sticky top-0 bg-card/100 (solid) border-b",
        "cells": "text-sm; numeric cells tabular-nums; truncate long names with tooltip",
        "row_hover": "hover:bg-muted/60",
        "empty_state": "Show centered Card with icon + CTA"
      },
      "charts_recharts": {
        "palette": [
          "hsl(var(--chart-1))",
          "hsl(var(--chart-2))",
          "hsl(var(--chart-3))",
          "hsl(var(--chart-4))",
          "hsl(var(--chart-5))"
        ],
        "grid": "CartesianGrid stroke='hsl(var(--gridline))' strokeDasharray='3 3'",
        "tooltip": "Use custom tooltip Card with bg-card text-foreground border",
        "axis": "tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}",
        "area_fill": "Use low-opacity fill (0.12–0.18) to avoid heavy gradients"
      },
      "navigation": {
        "sidebar": "Solid navy surface using --sidebar; section separators; active item uses saffron left border + subtle bg.",
        "topbar": "Solid surface; quick search centered-left; right cluster: sample mode badge, theme toggle, user menu.",
        "mobile": "Sidebar in Sheet; keep primary actions reachable with bottom padding."
      }
    }
  },

  "motion_microinteractions": {
    "libraries": {
      "framer_motion": {
        "use_cases": [
          "Page transitions (fade + slight y)",
          "KPI cards entrance stagger",
          "Filter sidebar open/close",
          "Tab underline animation"
        ],
        "rules": [
          "Respect prefers-reduced-motion",
          "No springy playful motion; keep it crisp (duration 0.18–0.28s)"
        ]
      }
    },
    "interaction_specs": [
      "Buttons: hover color shift only; press scale 0.98; focus ring saffron.",
      "Cards: hover elevate shadow + border; no transform on hover (keeps layout stable).",
      "Tables: row hover highlight; sticky header; column sort icon rotates 180deg.",
      "Sidebar: active item has animated left indicator (2px) using motion div.",
      "Search suggestions: Command palette opens with fade+scale 0.98->1."
    ]
  },

  "page_by_page": {
    "landing": {
      "layout": [
        "Hero: left text + right visual (Mumbai skyline image with subtle overlay).",
        "Live counter strip under hero (Card with monospace numbers).",
        "Feature grid: 2x2 cards with icons.",
        "Pricing preview: 3 cards + link to full pricing.",
        "CTA band: solid navy background with saffron button (no gradients)."
      ],
      "key_components": ["Card", "Button", "Badge", "Separator"],
      "data_testids": [
        "landing-hero-primary-cta",
        "landing-live-counter",
        "landing-feature-grid",
        "landing-pricing-preview"
      ]
    },
    "dashboard": {
      "layout": [
        "Top row KPI cards (4 on desktop, 2 per row on mobile).",
        "Charts row: line (trend) + donut (city) + bar (sectors) + bar (capital ranges).",
        "Recent activity feed: Table (last 10 new companies) with quick actions.",
        "Always-visible quick search in topbar; optional secondary quick search card in content for mobile."
      ],
      "data_testids": [
        "dashboard-kpi-total-companies",
        "dashboard-chart-registrations-trend",
        "dashboard-chart-city-distribution",
        "dashboard-recent-activity-table"
      ]
    },
    "search": {
      "layout": [
        "Left filter sidebar (desktop) with city/status/sector/date range/capital slider/class.",
        "Mobile: filters in Drawer with Apply/Reset sticky footer.",
        "Results header: count + sort Select + Save Search button.",
        "Results grid of company cards; pagination 50/page."
      ],
      "key_components": ["Drawer", "Select", "Slider", "Calendar", "Pagination", "Card"],
      "data_testids": [
        "search-filters-open-button",
        "search-results-count",
        "search-sort-select",
        "search-save-search-button",
        "search-pagination"
      ]
    },
    "company_detail": {
      "layout": [
        "Header: company name + status badge + city tag + key stats row.",
        "Tabs: Overview / Directors / Charges / Filings / Contact (Pro gated).",
        "Within tabs: tables with sticky headers; show skeletons while loading.",
        "Similar companies: 6 cards grid at bottom."
      ],
      "key_components": ["Tabs", "Table", "Badge", "Card", "Dialog"],
      "data_testids": [
        "company-header-name",
        "company-status-badge",
        "company-tabs",
        "company-similar-companies"
      ]
    },
    "analytics": {
      "layout": [
        "City selector tabs (All/Mumbai/Navi Mumbai/Thane) sticky on mobile.",
        "Full-width charts stacked: area trend, horizontal bar sectors, treemap/heatmap, capital distribution.",
        "Sector table below charts with search + export."
      ],
      "key_components": ["Tabs", "Card", "Table"],
      "data_testids": [
        "analytics-city-tabs",
        "analytics-trend-chart",
        "analytics-sectors-bar",
        "analytics-heatmap"
      ]
    },
    "alerts": {
      "layout": [
        "Create alert form (Card) with multi-select city/sector, min capital, frequency.",
        "My alerts table with enable Switch per row.",
        "Empty state: prompt to create first alert."
      ],
      "key_components": ["Form", "Select", "Switch", "Table"],
      "data_testids": [
        "alerts-create-form",
        "alerts-frequency-select",
        "alerts-submit-button",
        "alerts-table"
      ]
    },
    "export": {
      "layout": [
        "Filter panel (Card) + export options (CSV/Excel/PDF) as segmented buttons.",
        "Usage meter (Progress) with exports remaining.",
        "Export history table (optional)."
      ],
      "key_components": ["Progress", "Button", "Card", "Table"],
      "data_testids": [
        "export-format-csv",
        "export-format-excel",
        "export-format-pdf",
        "export-usage-meter"
      ]
    },
    "pricing": {
      "layout": [
        "4 tier cards; Pro highlighted with saffron border + subtle background.",
        "Feature comparison table below.",
        "FAQ accordion at bottom."
      ],
      "key_components": ["Card", "Table", "Accordion"],
      "data_testids": [
        "pricing-tier-free",
        "pricing-tier-pro",
        "pricing-compare-table",
        "pricing-upgrade-cta"
      ]
    },
    "settings": {
      "layout": [
        "Account info card + plan status card + usage stats.",
        "Saved searches list + alerts list.",
        "API key (Pro+) with copy button + reveal toggle.",
        "Billing/upgrade CTA."
      ],
      "key_components": ["Card", "Tabs", "Button", "Input"],
      "data_testids": [
        "settings-account-card",
        "settings-plan-status",
        "settings-api-key-copy-button",
        "settings-upgrade-button"
      ]
    }
  },

  "images": {
    "image_urls": [
      {
        "category": "landing_hero",
        "description": "Mumbai skyline image for hero right-side visual; apply subtle navy overlay for readability.",
        "url": "https://images.unsplash.com/photo-1578993074370-5865598d5b1e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHwxfHxtdW1iYWklMjBza3lsaW5lJTIwZHVzayUyMG1pbmltYWx8ZW58MHx8fGJsdWV8MTc4Mjc2NzAwOHww&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "landing_secondary",
        "description": "Alternate Mumbai waterfront visual for secondary sections (pricing preview background image in a small card).",
        "url": "https://images.unsplash.com/photo-1567870374047-3f9db5c06b16?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHwzfHxtdW1iYWklMjBza3lsaW5lJTIwZHVzayUyMG1pbmltYWx8ZW58MHx8fGJsdWV8MTc4Mjc2NzAwOHww&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "marketing_background",
        "description": "Cityscape for subtle banner usage (keep under 20% viewport; avoid gradients over text).",
        "url": "https://images.unsplash.com/photo-1661527188297-35e762c4519b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHwyfHxtdW1iYWklMjBza3lsaW5lJTIwZHVzayUyMG1pbmltYWx8ZW58MHx8fGJsdWV8MTc4Mjc2NzAwOHww&ixlib=rb-4.1.0&q=85"
      }
    ]
  },

  "accessibility": {
    "rules": [
      "WCAG AA contrast: ensure saffron text is only used on dark/navy surfaces or as background with dark text (accent-foreground).",
      "Focus states: always visible (ring saffron + ring-offset).",
      "Touch targets: minimum 44px height for primary actions on mobile.",
      "Do not rely on color alone for status; include label + icon.",
      "Respect prefers-reduced-motion: disable entrance animations and reduce durations."
    ]
  },

  "testing_attributes": {
    "data_testid_rules": [
      "Use kebab-case describing role, not appearance.",
      "Apply to: buttons, links, inputs, selects, sliders, switches, pagination controls, tabs triggers, key KPI values, error banners, empty states CTAs.",
      "Examples: data-testid=\"company-card-track-button\", data-testid=\"search-filter-city-select\""
    ]
  },

  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css shadcn tokens to the provided HSL values for :root and .dark; add extra custom properties for sidebar/topbar/surfaces.",
    "Remove CRA demo styles from /app/frontend/src/App.css (logo spin etc.) and keep App.css minimal or empty; rely on Tailwind.",
    "Implement app shell: Sidebar (desktop) + Sheet (mobile) + Topbar with quick search (Command) + theme toggle (next-themes).",
    "Use shadcn components from /src/components/ui only (no raw HTML dropdowns/calendars/toasts).",
    "Charts: Recharts with palette from --chart-*; custom tooltip Card; avoid heavy gradients.",
    "Ensure every interactive + key informational element includes data-testid.",
    "Keep density high but calm: use separators, muted text, and consistent spacing; avoid centered layouts."
  ],

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
