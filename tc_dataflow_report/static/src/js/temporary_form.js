(function () {
    function serializeFormState(form) {
        var fields = Array.prototype.slice.call(
            form.querySelectorAll("input[name], select[name], textarea[name]")
        ).filter(function (field) {
            return field.type !== "hidden" && field.type !== "submit" && field.type !== "button" && !field.disabled && !field.readOnly;
        });

        var state = {};
        fields.forEach(function (field) {
            if (field.type === "radio") {
                if (!Object.prototype.hasOwnProperty.call(state, field.name)) {
                    state[field.name] = "";
                }
                if (field.checked) {
                    state[field.name] = field.value || "";
                }
                return;
            }

            if (field.type === "checkbox") {
                state[field.name] = field.checked ? "1" : "0";
                return;
            }

            state[field.name] = field.value || "";
        });
        return JSON.stringify(state);
    }

    function initTemporaryForm() {
        var app = document.querySelector("[data-provisional-app]");
        if (!app) {
            return;
        }

        var form = app.querySelector("form");
        var saveDraftButton = app.querySelector("[data-provisional-save-draft]");
        var modeTriggers = Array.prototype.slice.call(app.querySelectorAll("[data-provisional-mode-trigger]"));
        var modePanels = Array.prototype.slice.call(app.querySelectorAll("[data-provisional-mode-panel]"));
        var modePicker = app.querySelector("[data-provisional-mode-picker]");
        var modeSummary = app.querySelector("[data-provisional-mode-summary]");
        var modeLabel = app.querySelector("[data-provisional-mode-label]");
        var modeDescription = app.querySelector("[data-provisional-mode-description]");
        var initialState = "";
        var saveDraftStateKey = "";

        if (form) {
            var entryIdField = form.querySelector("input[name='entry_id']");
            saveDraftStateKey = "tc_provisional_saved_state:" + (entryIdField && entryIdField.value ? entryIdField.value : "new");
        }

        function getSavedState() {
            if (!saveDraftStateKey || !window.sessionStorage) {
                return "";
            }
            return window.sessionStorage.getItem(saveDraftStateKey) || "";
        }

        function setSavedState(nextState) {
            if (!saveDraftStateKey || !window.sessionStorage) {
                return;
            }
            window.sessionStorage.setItem(saveDraftStateKey, nextState);
        }

        function setSaveDraftVisibility() {
            if (!form || !saveDraftButton) {
                return;
            }
            saveDraftButton.hidden = serializeFormState(form) === initialState;
        }

        function closeModePicker() {
            if (!modePicker) {
                return;
            }
            modePicker.classList.remove("is-open");
        }

        function updateModeSummary(nextMode) {
            var activeTrigger = modeTriggers.find(function (trigger) {
                return trigger.value === nextMode;
            });
            if (!activeTrigger) {
                return;
            }

            if (modeLabel) {
                modeLabel.textContent = activeTrigger.dataset.provisionalOptionLabel || "";
            }
            if (modeDescription) {
                modeDescription.textContent = activeTrigger.dataset.provisionalOptionDescription || "";
            }
        }

        function syncModePanel(panel, isActive) {
            var fields = Array.prototype.slice.call(panel.querySelectorAll("input, select, textarea"));
            if (isActive) {
                panel.removeAttribute("hidden");
            } else {
                panel.setAttribute("hidden", "hidden");
            }

            fields.forEach(function (field) {
                if (!field.dataset.provisionalBaseDisabled) {
                    field.dataset.provisionalBaseDisabled = field.disabled ? "1" : "0";
                }
                field.disabled = !isActive || field.dataset.provisionalBaseDisabled === "1";
            });
        }

        function setActiveMode(nextMode) {
            modeTriggers.forEach(function (trigger) {
                var isActive = trigger.value === nextMode;
                var card = trigger.closest(".tc-temporary-toggle-card");
                if (card) {
                    card.classList.toggle("is-active", isActive);
                }
            });

            modePanels.forEach(function (panel) {
                syncModePanel(panel, panel.dataset.provisionalModePanel === nextMode);
            });
            updateModeSummary(nextMode);
        }

        if (form) {
            form.addEventListener("input", setSaveDraftVisibility);
            form.addEventListener("change", setSaveDraftVisibility);
            form.addEventListener("submit", function (event) {
                var submitter = event.submitter;
                if (!submitter || !submitter.hasAttribute("data-provisional-save-draft")) {
                    return;
                }
                initialState = serializeFormState(form);
                setSavedState(initialState);
                setSaveDraftVisibility();
            });
        }

        if (modeSummary) {
            modeSummary.addEventListener("click", function () {
                if (modeSummary.disabled || !modePicker) {
                    return;
                }
                modePicker.classList.toggle("is-open");
            });
        }

        modeTriggers.forEach(function (trigger) {
            trigger.addEventListener("change", function () {
                if (!trigger.checked) {
                    return;
                }
                setActiveMode(trigger.value);
                closeModePicker();
                setSaveDraftVisibility();
            });
        });

        document.addEventListener("click", function (event) {
            if (!modePicker || modePicker.contains(event.target)) {
                return;
            }
            closeModePicker();
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeModePicker();
            }
        });

        var checkedMode = modeTriggers.find(function (trigger) {
            return trigger.checked;
        });
        setActiveMode(checkedMode ? checkedMode.value : "auto");
        initialState = form ? serializeFormState(form) : "";
        if (getSavedState() === initialState) {
            initialState = getSavedState();
        } else {
            setSavedState(initialState);
        }
        setSaveDraftVisibility();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initTemporaryForm);
        return;
    }

    initTemporaryForm();
})();
