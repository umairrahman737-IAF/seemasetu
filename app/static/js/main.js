/**
 * SeemaSetu — Interactive Frontend Behaviors
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Alert Dismiss Buttons
  document.querySelectorAll('.alert-close').forEach(function (button) {
    button.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.25s ease';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 2. Real-time Live Priority Score Preview on Issue Form
  const issueForm = document.getElementById('issue-report-form');
  if (issueForm) {
    const sevSelect = document.getElementById('severity-select');
    const urgSelect = document.getElementById('urgency-select');
    const catSelect = document.getElementById('category-select');
    const weaSelect = document.getElementById('weather-select');

    const scoreValue = document.getElementById('preview-score-value');
    const levelBadge = document.getElementById('preview-level-badge');
    const progressFill = document.getElementById('preview-progress-fill');
    const recommendationText = document.getElementById('preview-recommendation');

    function updatePriorityPreview() {
      if (!sevSelect || !urgSelect || !catSelect || !weaSelect) return;

      const payload = {
        severity: sevSelect.value,
        urgency: urgSelect.value,
        category: catSelect.value,
        weather_vulnerability: weaSelect.value
      };

      fetch('/api/calculate-priority-preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(res => {
        if (res.status === 'success') {
          const data = res.data;
          if (scoreValue) scoreValue.textContent = data.score + '/100';
          if (recommendationText) recommendationText.textContent = data.recommendation;

          if (progressFill) {
            progressFill.style.width = data.score + '%';
            if (data.score >= 75) {
              progressFill.style.backgroundColor = '#dc2626';
            } else if (data.score >= 55) {
              progressFill.style.backgroundColor = '#ea580c';
            } else if (data.score >= 35) {
              progressFill.style.backgroundColor = '#d97706';
            } else {
              progressFill.style.backgroundColor = '#0284c7';
            }
          }

          if (levelBadge) {
            levelBadge.textContent = data.level;
            levelBadge.className = 'badge ' + data.badge_class;
          }
        }
      })
      .catch(err => console.debug('Priority calculation preview sync error:', err));
    }

    [sevSelect, urgSelect, catSelect, weaSelect].forEach(el => {
      if (el) el.addEventListener('change', updatePriorityPreview);
    });

    // Run initial update on load
    updatePriorityPreview();
  }

  // 3. Work Order Progress Slider live number display
  const progressSlider = document.getElementById('progress-slider');
  const progressValueDisplay = document.getElementById('progress-slider-val');
  if (progressSlider && progressValueDisplay) {
    progressSlider.addEventListener('input', function () {
      progressValueDisplay.textContent = this.value + '%';
    });
  }

  // 4. Confirmation on high-impact buttons
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const message = this.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
