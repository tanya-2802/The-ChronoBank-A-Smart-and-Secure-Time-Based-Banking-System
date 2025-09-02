// ChronoBank Main JavaScript

document.addEventListener("DOMContentLoaded", () => {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Time conversion utilities
  window.timeUtils = {
    // Convert seconds to human-readable format
    formatTime: (seconds) => {
      const days = Math.floor(seconds / 86400)
      seconds %= 86400
      const hours = Math.floor(seconds / 3600)
      seconds %= 3600
      const minutes = Math.floor(seconds / 60)
      seconds %= 60

      const result = []
      if (days > 0) result.push(`${days} day${days !== 1 ? "s" : ""}`)
      if (hours > 0) result.push(`${hours} hour${hours !== 1 ? "s" : ""}`)
      if (minutes > 0) result.push(`${minutes} minute${minutes !== 1 ? "s" : ""}`)
      if (seconds > 0 || result.length === 0) result.push(`${seconds} second${seconds !== 1 ? "s" : ""}`)

      return result.join(", ")
    },

    // Convert human input to seconds
    parseTimeInput: (input) => {
      // Format: 1d 2h 3m 4s or variations
      let seconds = 0
      const days = input.match(/(\d+)\s*d/i)
      const hours = input.match(/(\d+)\s*h/i)
      const minutes = input.match(/(\d+)\s*m(?!s)/i)
      const secs = input.match(/(\d+)\s*s/i)

      if (days) seconds += Number.parseInt(days[1]) * 86400
      if (hours) seconds += Number.parseInt(hours[1]) * 3600
      if (minutes) seconds += Number.parseInt(minutes[1]) * 60
      if (secs) seconds += Number.parseInt(secs[1])

      return seconds
    },
  }

  // Handle time input conversion in forms
  const timeInputs = document.querySelectorAll(".time-input")
  if (timeInputs.length > 0) {
    timeInputs.forEach((input) => {
      input.addEventListener("change", function () {
        const secondsInput = document.getElementById(this.dataset.target)
        if (secondsInput) {
          secondsInput.value = window.timeUtils.parseTimeInput(this.value)
        }
      })
    })
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert:not(.alert-permanent)")
  if (alerts.length > 0) {
    alerts.forEach((alert) => {
      setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert)
        bsAlert.close()
      }, 5000)
    })
  }

  // Account balance progress bars
  const progressBars = document.querySelectorAll(".progress-bar")
  if (progressBars.length > 0) {
    progressBars.forEach((bar) => {
      const value = Number.parseFloat(bar.style.width)
      if (value < 30) {
        bar.classList.remove("bg-primary")
        bar.classList.add("bg-danger")
      } else if (value < 70) {
        bar.classList.remove("bg-primary")
        bar.classList.add("bg-warning")
      }
    })
  }

  // Transaction amount helper
  const amountInputs = document.querySelectorAll('input[name="amount"]')
  if (amountInputs.length > 0) {
    amountInputs.forEach((input) => {
      const helper = document.createElement("div")
      helper.className = "form-text mt-2"
      helper.id = "amount-helper"
      input.parentNode.appendChild(helper)

      input.addEventListener("input", function () {
        const seconds = Number.parseInt(this.value) || 0
        helper.textContent = `Equivalent to: ${window.timeUtils.formatTime(seconds)}`
      })

      // Trigger on load
      input.dispatchEvent(new Event("input"))
    })
  }
})
