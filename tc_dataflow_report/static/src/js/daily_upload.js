(function () {
    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function getSections() {
        return Array.prototype.slice.call(document.querySelectorAll(".tc-daily-section[data-section-key]"));
    }

    function getFilterInput() {
        return document.querySelector("[data-upload-filter-date]");
    }

    function getCurrentFilterDate() {
        var filterInput = getFilterInput();
        return filterInput ? filterInput.value : "";
    }

    function getRecentDaysRoot() {
        return document.querySelector("[data-recent-days]");
    }

    function getSelectedDateDisplay() {
        return document.querySelector("[data-selected-date-display]");
    }

    function getWorkspaceMode() {
        var sectionsRoot = document.querySelector("[data-daily-sections]");
        return sectionsRoot ? String(sectionsRoot.dataset.dailyWorkspace || "daily") : "daily";
    }

    function getSubmitButton(section) {
        var targetSection = section || getActiveSection();
        return targetSection ? targetSection.querySelector("[data-submit-approval]") : null;
    }

    function getActiveSection() {
        return document.querySelector('.tc-daily-section[data-section-key].is-active') || getSections()[0] || null;
    }

    function getSectionState(section) {
        if (!section._tcDailyUploadState) {
            var pagination = section.querySelector("[data-preview-pagination]");
            section._tcDailyUploadState = {
                files: [],
                checkingCount: parseInt(section.dataset.checkingCount || "0", 10) || 0,
                hideUploadZone: section.dataset.hideUploadZone === "1",
                openFileId: "",
                preview: {
                    page: pagination ? parseInt(pagination.dataset.previewPage || "1", 10) || 1 : 1,
                    totalPages: pagination ? parseInt(pagination.dataset.previewTotalPages || "1", 10) || 1 : 1,
                    hasPrev: pagination ? pagination.dataset.previewHasPrev === "1" : false,
                    hasNext: pagination ? pagination.dataset.previewHasNext === "1" : false,
                    loading: false,
                },
            };
        }
        return section._tcDailyUploadState;
    }

    function setSectionFeedback(section, message, type) {
        var feedback = section ? section.querySelector("[data-upload-feedback]") : null;
        if (!feedback) {
            return;
        }
        feedback.textContent = message || "";
        feedback.hidden = !message;
        feedback.classList.toggle("is-success", type === "success");
        feedback.classList.toggle("is-error", type === "error");
    }

    function renderRecentDays(recentDays) {
        var root = getRecentDaysRoot();
        if (!root) {
            return;
        }

        root.innerHTML = (recentDays || []).map(function (day) {
            return [
                '<article class="tc-dashboard-timeline__item ' + escapeHtml(day.status_class || "is-pending") + '">',
                '<div class="tc-dashboard-timeline__row">',
                "<strong>" + escapeHtml(day.date) + "</strong>",
                "<span>" + escapeHtml(day.status) + "</span>",
                "</div>",
                "<p>" + escapeHtml(day.note) + "</p>",
                "</article>",
            ].join("");
        }).join("");
    }

    function updateSharedState(payload) {
        var filterInput = getFilterInput();
        var selectedDateDisplay = getSelectedDateDisplay();

        if (filterInput && payload.selected_date_input) {
            filterInput.value = payload.selected_date_input;
        }
        if (selectedDateDisplay && payload.selected_date_display) {
            selectedDateDisplay.textContent = payload.selected_date_display;
        }
        if (payload.recent_days) {
            renderRecentDays(payload.recent_days);
        }
    }

    function updateSubmitState() {
        var activeSection = getActiveSection();
        if (!activeSection) {
            return;
        }

        getSections().forEach(function (section) {
            var submitButton = getSubmitButton(section);
            if (!submitButton) {
                return;
            }
            var state = getSectionState(section);
            var checkingCount = state.checkingCount || parseInt(section.dataset.checkingCount || "0", 10) || 0;
            submitButton.disabled = state.hideUploadZone || checkingCount <= 0;
        });
    }

    function renderUploadZone(section, hideUploadZone) {
        var zone = section.querySelector("[data-upload-zone]");
        var state = getSectionState(section);
        var submitButton = getSubmitButton(section);
        if (!zone) {
            return;
        }
        state.hideUploadZone = !!hideUploadZone;
        section.dataset.hideUploadZone = state.hideUploadZone ? "1" : "0";
        zone.hidden = state.hideUploadZone;
        if (submitButton) {
            submitButton.disabled = state.hideUploadZone || state.checkingCount <= 0;
        }
    }

    function renderUploadedFiles(section, files, checkingCount) {
        var body = section.querySelector("[data-uploaded-files-body]");
        var state = getSectionState(section);
        if (!body) {
            return;
        }

        state.files = files || [];
        state.checkingCount = typeof checkingCount === "number"
            ? checkingCount
            : state.files.filter(function (file) { return file.status_code === "checking"; }).length;
        section.dataset.checkingCount = String(state.checkingCount);
        if (!state.files.length) {
            body.innerHTML = [
                '<tr class="tc-dashboard-table__empty">',
                '<td colspan="6">Chua co file nao duoc tai len.</td>',
                "</tr>",
            ].join("");
            updateSubmitState();
            return;
        }

        body.innerHTML = state.files.map(function (file) {
            var actions = (file.actions || []).map(function (action) {
                var disabledAttr = action.disabled ? " disabled" : "";
                var actionKeyAttr = action.key ? ' data-action-key="' + escapeHtml(action.key) + '"' : "";
                var fileIdAttr = file.id ? ' data-file-id="' + escapeHtml(file.id) + '"' : "";
                var styleClass = action.style ? " is-" + escapeHtml(action.style) : "";
                return [
                    '<button type="button" class="tc-dashboard-table__action' + styleClass + '"' + actionKeyAttr + fileIdAttr + disabledAttr + ">",
                    '<span class="material-symbols-outlined">' + escapeHtml(action.icon || "visibility") + "</span>",
                    escapeHtml(action.label),
                    "</button>",
                ].join("");
            }).join("");

            return [
                "<tr>",
                '<td class="is-strong">' + escapeHtml(file.name) + "</td>",
                "<td>" + escapeHtml(file.version) + "</td>",
                "<td>" + escapeHtml(file.uploaded_at_display) + "</td>",
                "<td>" + escapeHtml(file.size_display) + "</td>",
                "<td>",
                '<span class="tc-dashboard-status ' + escapeHtml(file.status_class) + '">',
                '<span class="material-symbols-outlined">' + escapeHtml(file.status_icon) + "</span>",
                escapeHtml(file.status),
                "</span>",
                "</td>",
                '<td class="is-right"><div class="tc-dashboard-table__actions">' + actions + "</div></td>",
                "</tr>",
            ].join("");
        }).join("");
        updateSubmitState();
    }

    function setPreviewLoading(section, isLoading) {
        var state = getSectionState(section);
        var pagination = section.querySelector("[data-preview-pagination]");
        var prevButton = section.querySelector('[data-preview-page-action="prev"]');
        var nextButton = section.querySelector('[data-preview-page-action="next"]');

        state.preview.loading = isLoading;
        if (pagination) {
            pagination.classList.toggle("is-loading", isLoading);
        }
        if (prevButton) {
            prevButton.disabled = isLoading || !state.preview.hasPrev;
        }
        if (nextButton) {
            nextButton.disabled = isLoading || !state.preview.hasNext;
        }
    }

    function renderPreviewPagination(section, columns, paginationInfo) {
        var pagination = section.querySelector("[data-preview-pagination]");
        var summary = section.querySelector("[data-preview-summary]");
        var label = section.querySelector("[data-preview-page-label]");
        var prevButton = section.querySelector('[data-preview-page-action="prev"]');
        var nextButton = section.querySelector('[data-preview-page-action="next"]');
        var state = getSectionState(section);

        if (!pagination || !summary || !label || !prevButton || !nextButton) {
            return;
        }

        if (!columns || !columns.length) {
            state.preview.page = 1;
            state.preview.totalPages = 1;
            state.preview.hasPrev = false;
            state.preview.hasNext = false;
            pagination.hidden = true;
            return;
        }

        var normalizedPagination = paginationInfo || {};
        state.preview.page = normalizedPagination.page || 1;
        state.preview.totalPages = normalizedPagination.total_pages || 1;
        state.preview.hasPrev = !!normalizedPagination.has_prev;
        state.preview.hasNext = !!normalizedPagination.has_next;

        pagination.dataset.previewPage = String(state.preview.page);
        pagination.dataset.previewTotalPages = String(state.preview.totalPages);
        pagination.dataset.previewHasPrev = state.preview.hasPrev ? "1" : "0";
        pagination.dataset.previewHasNext = state.preview.hasNext ? "1" : "0";
        pagination.hidden = false;
        summary.textContent = normalizedPagination.summary || "";
        label.textContent = "Trang " + String(state.preview.page) + " / " + String(state.preview.totalPages);
        prevButton.disabled = state.preview.loading || !state.preview.hasPrev;
        nextButton.disabled = state.preview.loading || !state.preview.hasNext;
    }

    function renderPreview(section, columns, rows, paginationInfo) {
        var table = section.querySelector("[data-preview-table]");
        var head = section.querySelector("[data-preview-head]");
        var body = section.querySelector("[data-preview-body]");
        var empty = section.querySelector("[data-preview-empty]");
        if (!table || !head || !body || !empty) {
            return;
        }

        if (!columns || !columns.length) {
            head.innerHTML = "";
            body.innerHTML = "";
            table.hidden = true;
            empty.hidden = false;
            renderPreviewPagination(section, [], null);
            return;
        }

        head.innerHTML = columns.map(function (column) {
            var headerClass = column.header_class ? ' class="' + escapeHtml(column.header_class) + '"' : "";
            return "<th" + headerClass + ">" + escapeHtml(column.label) + "</th>";
        }).join("");

        if (!rows || !rows.length) {
            body.innerHTML = [
                '<tr class="tc-dashboard-table__empty">',
                '<td colspan="' + String(columns.length) + '">File da duoc doc nhung chua co dong du lieu de hien thi.</td>',
                "</tr>",
            ].join("");
        } else {
            body.innerHTML = rows.map(function (row) {
                return [
                    "<tr>",
                    columns.map(function (column) {
                        var cellClass = column.cell_class ? ' class="' + escapeHtml(column.cell_class) + '"' : "";
                        return "<td" + cellClass + ">" + escapeHtml(row[column.field]) + "</td>";
                    }).join(""),
                    "</tr>",
                ].join("");
            }).join("");
        }

        table.hidden = false;
        empty.hidden = true;
        renderPreviewPagination(section, columns, paginationInfo);
    }

    function applySectionPayload(section, payload) {
        var state = getSectionState(section);
        state.openFileId = payload.current_file_id ? String(payload.current_file_id) : "";
        renderUploadZone(section, payload.hide_upload_zone);
        renderUploadedFiles(section, payload.uploaded_files || [], payload.checking_count);
        renderPreview(section, payload.preview_columns || [], payload.preview_rows || [], payload.preview_pagination || null);
    }

    function applySharedSectionPayload(section, payload) {
        updateSharedState(payload);
        applySectionPayload(section, payload);
    }

    function readJsonResponse(response) {
        return response.json().catch(function () {
            return {
                success: false,
                message: "Khong doc duoc phan hoi tu may chu.",
            };
        }).then(function (payload) {
            if (!response.ok && payload.success === undefined) {
                payload.success = false;
            }
            return payload;
        });
    }

    function applyFilterPayload(payload) {
        updateSharedState(payload);
        getSections().forEach(function (section) {
            var sectionPayload = payload.sections && payload.sections[section.dataset.sectionKey];
            if (sectionPayload) {
                applySectionPayload(section, sectionPayload);
                setSectionFeedback(section, "", null);
            }
        });
        updateSubmitState();
    }

    function requestFilterState(filterDate) {
        var activeSection = getActiveSection();
        var url = "/home/daily/filter?filter_date=" + encodeURIComponent(filterDate || "");
        url += "&workspace=" + encodeURIComponent(getWorkspaceMode());
        if (activeSection) {
            setSectionFeedback(activeSection, "Dang cap nhat danh sach file theo ngay tai len...", null);
        }

        fetch(url, {
            method: "GET",
            credentials: "same-origin",
        })
            .then(readJsonResponse)
            .then(function (payload) {
                if (!payload.success) {
                    if (activeSection) {
                        setSectionFeedback(activeSection, payload.message || "Khong the loc du lieu.", "error");
                    }
                    return;
                }
                applyFilterPayload(payload);
            })
            .catch(function () {
                if (activeSection) {
                    setSectionFeedback(activeSection, "Khong the cap nhat bo loc luc nay.", "error");
                }
            });
    }

    function requestPreviewState(section, fileId, page) {
        var state = getSectionState(section);
        var parsedPage = parseInt(page || "1", 10) || 1;
        var url = "/home/daily/preview?section=" + encodeURIComponent(section.dataset.sectionKey || "") + "&page=" + encodeURIComponent(String(parsedPage));
        url += "&filter_date=" + encodeURIComponent(getCurrentFilterDate());
        url += "&workspace=" + encodeURIComponent(getWorkspaceMode());
        if (fileId) {
            url += "&file_id=" + encodeURIComponent(String(fileId));
        }

        setPreviewLoading(section, true);

        fetch(url, {
            method: "GET",
            credentials: "same-origin",
        })
            .then(readJsonResponse)
            .then(function (payload) {
                if (!payload.success) {
                    setSectionFeedback(section, payload.message || "Khong the tai preview.", "error");
                    return;
                }
                applySharedSectionPayload(section, payload);
            })
            .catch(function () {
                setSectionFeedback(section, "Khong the tai preview luc nay.", "error");
            })
            .finally(function () {
                setPreviewLoading(section, false);
            });
    }

    function initUploadSection(section) {
        var zone = section.querySelector("[data-upload-zone]");
        var input = section.querySelector("[data-upload-input]");
        var trigger = section.querySelector("[data-upload-trigger]");
        var filesBody = section.querySelector("[data-uploaded-files-body]");
        var pagination = section.querySelector("[data-preview-pagination]");
        if (!zone || !input || !trigger) {
            return;
        }

        getSectionState(section);

        function setUploading(isUploading) {
            zone.classList.toggle("is-uploading", isUploading);
            trigger.disabled = isUploading;
            input.disabled = isUploading;
        }

        function openFilePicker() {
            if (!input.disabled) {
                input.click();
            }
        }

        function uploadFile(file) {
            if (!file) {
                return;
            }

            var formData = new FormData();
            formData.append("section", section.dataset.sectionKey || "");
            formData.append("filter_date", getCurrentFilterDate());
            formData.append("workspace", getWorkspaceMode());
            formData.append("file", file);

            setUploading(true);
            setSectionFeedback(section, "Dang doc file Excel va dua vao trang thai kiem tra...", null);

            fetch("/home/daily/upload", {
                method: "POST",
                body: formData,
                credentials: "same-origin",
            })
                .then(readJsonResponse)
                .then(function (payload) {
                    applySharedSectionPayload(section, payload);
                    setSectionFeedback(section, payload.message || "Da xu ly xong.", payload.success ? "success" : "error");
                })
                .catch(function () {
                    setSectionFeedback(section, "Khong the tai file len luc nay.", "error");
                })
                .finally(function () {
                    setUploading(false);
                    input.value = "";
                    zone.classList.remove("is-dragover");
                });
        }

        function reviewFile(fileId, route, pendingMessage, successFallback) {
            if (!fileId) {
                return;
            }

            var formData = new FormData();
            formData.append("section", section.dataset.sectionKey || "");
            formData.append("file_id", fileId);
            formData.append("filter_date", getCurrentFilterDate());
            formData.append("workspace", getWorkspaceMode());

            setSectionFeedback(section, pendingMessage, null);

            fetch(route, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
            })
                .then(readJsonResponse)
                .then(function (payload) {
                    applySharedSectionPayload(section, payload);
                    setSectionFeedback(section, payload.message || successFallback, payload.success ? "success" : "error");
                })
                .catch(function () {
                    setSectionFeedback(section, "Khong the xu ly thao tac nay luc nay.", "error");
                });
        }

        trigger.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            openFilePicker();
        });

        zone.addEventListener("click", function (event) {
            if (event.target.closest("[data-upload-trigger]")) {
                return;
            }
            openFilePicker();
        });

        zone.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openFilePicker();
            }
        });

        input.addEventListener("change", function () {
            uploadFile(input.files && input.files[0]);
        });

        if (filesBody) {
            filesBody.addEventListener("click", function (event) {
                var actionButton = event.target.closest("[data-action-key]");
                var state = getSectionState(section);
                if (!actionButton || actionButton.disabled) {
                    return;
                }

                event.preventDefault();
                if (actionButton.dataset.actionKey === "submit") {
                    reviewFile(actionButton.dataset.fileId, "/home/daily/submit", "Dang gui file sang Approvals...", "Da gui phe duyet file.");
                    return;
                }
                if (actionButton.dataset.actionKey === "approve") {
                    reviewFile(actionButton.dataset.fileId, "/home/daily/approve", "Dang phe duyet file...", "Da phe duyet file.");
                    return;
                }
                if (actionButton.dataset.actionKey === "reject") {
                    reviewFile(actionButton.dataset.fileId, "/home/daily/reject", "Dang tu choi file...", "Da tu choi file.");
                    return;
                }
                if (actionButton.dataset.actionKey === "toggle_detail") {
                    if (state.openFileId && state.openFileId === String(actionButton.dataset.fileId || "")) {
                        requestPreviewState(section, "", 1);
                    } else {
                        requestPreviewState(section, actionButton.dataset.fileId, 1);
                    }
                }
            });
        }

        if (pagination) {
            pagination.addEventListener("click", function (event) {
                var actionButton = event.target.closest("[data-preview-page-action]");
                var state = getSectionState(section);
                var nextPage = state.preview.page;
                if (!actionButton || actionButton.disabled || !state.openFileId) {
                    return;
                }

                if (actionButton.dataset.previewPageAction === "prev") {
                    nextPage -= 1;
                }
                if (actionButton.dataset.previewPageAction === "next") {
                    nextPage += 1;
                }
                requestPreviewState(section, state.openFileId, nextPage);
            });
        }

        ["dragenter", "dragover"].forEach(function (eventName) {
            zone.addEventListener(eventName, function (event) {
                event.preventDefault();
                zone.classList.add("is-dragover");
            });
        });

        ["dragleave", "dragend", "drop"].forEach(function (eventName) {
            zone.addEventListener(eventName, function (event) {
                event.preventDefault();
                zone.classList.remove("is-dragover");
            });
        });

        zone.addEventListener("drop", function (event) {
            var files = event.dataTransfer && event.dataTransfer.files;
            uploadFile(files && files[0]);
        });
    }

    function requestSubmitApproval() {
        var activeSection = getActiveSection();
        if (!activeSection) {
            return;
        }

        var formData = new FormData();
        formData.append("section", activeSection.dataset.sectionKey || "");
        formData.append("filter_date", getCurrentFilterDate());
        formData.append("workspace", getWorkspaceMode());
        setSectionFeedback(activeSection, "Dang gui file sang Approvals...", null);

        fetch("/home/daily/submit", {
            method: "POST",
            body: formData,
            credentials: "same-origin",
        })
            .then(readJsonResponse)
            .then(function (payload) {
                applySharedSectionPayload(activeSection, payload);
                setSectionFeedback(activeSection, payload.message || "Da gui phe duyet.", payload.success ? "success" : "error");
            })
            .catch(function () {
                setSectionFeedback(activeSection, "Khong the gui phe duyet luc nay.", "error");
            });
    }

    function initDailyUploads() {
        var sections = getSections();
        var filterInput = getFilterInput();
        if (!sections.length) {
            return;
        }
        sections.forEach(function (section) {
            initUploadSection(section);
            var submitButton = getSubmitButton(section);
            if (!submitButton) {
                return;
            }
            submitButton.addEventListener("click", function (event) {
                event.preventDefault();
                if (submitButton.disabled) {
                    return;
                }
                requestSubmitApproval();
            });
        });

        if (filterInput) {
            filterInput.addEventListener("change", function () {
                requestFilterState(filterInput.value || "");
            });
        }

        document.addEventListener("tc-daily-tab-change", updateSubmitState);
        updateSubmitState();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDailyUploads);
        return;
    }

    initDailyUploads();
})();
