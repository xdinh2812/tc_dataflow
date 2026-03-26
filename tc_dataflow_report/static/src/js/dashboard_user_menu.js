(function () {
    function getAccountUrl() {
        return fetch("/web/session/account", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {},
            }),
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (payload) {
                return payload && payload.result ? payload.result : "https://accounts.odoo.com/account";
            })
            .catch(function () {
                return "https://accounts.odoo.com/account";
            });
    }

    function closeMenu(menu) {
        var trigger = menu.querySelector("[data-user-menu-trigger]");
        var panel = menu.querySelector("[data-user-menu-panel]");
        if (!trigger || !panel) {
            return;
        }
        menu.classList.remove("is-open");
        panel.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
    }

    function openMenu(menu) {
        var trigger = menu.querySelector("[data-user-menu-trigger]");
        var panel = menu.querySelector("[data-user-menu-panel]");
        if (!trigger || !panel) {
            return;
        }
        menu.classList.add("is-open");
        panel.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
    }

    function updateOnlineState(menu) {
        var statusLabel = menu.querySelector("[data-user-menu-status-label]");
        var statusDot = menu.querySelector("[data-user-menu-status-dot]");
        if (!statusLabel || !statusDot) {
            return;
        }
        var isOnline = navigator.onLine !== false;
        statusLabel.textContent = isOnline ? "Online" : "Offline";
        statusDot.classList.toggle("is-offline", !isOnline);
    }

    function initUserMenu(menu, allMenus) {
        var trigger = menu.querySelector("[data-user-menu-trigger]");
        var panel = menu.querySelector("[data-user-menu-panel]");
        var accountButton = menu.querySelector("[data-user-menu-account]");
        if (!trigger || !panel) {
            return;
        }

        updateOnlineState(menu);
        window.addEventListener("online", function () {
            updateOnlineState(menu);
        });
        window.addEventListener("offline", function () {
            updateOnlineState(menu);
        });

        trigger.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            var isOpen = menu.classList.contains("is-open");
            allMenus.forEach(closeMenu);
            if (!isOpen) {
                openMenu(menu);
            }
        });

        if (accountButton) {
            accountButton.addEventListener("click", function (event) {
                event.preventDefault();
                getAccountUrl().then(function (url) {
                    window.open(url, "_blank", "noopener,noreferrer");
                });
                closeMenu(menu);
            });
        }

        panel.addEventListener("click", function (event) {
            if (event.target.closest("a")) {
                closeMenu(menu);
            }
        });
    }

    function initUserMenus() {
        var menus = Array.prototype.slice.call(document.querySelectorAll("[data-user-menu]"));
        if (!menus.length) {
            return;
        }

        menus.forEach(function (menu) {
            initUserMenu(menu, menus);
        });

        document.addEventListener("click", function (event) {
            menus.forEach(function (menu) {
                if (!menu.contains(event.target)) {
                    closeMenu(menu);
                }
            });
        });

        document.addEventListener("keydown", function (event) {
            if (event.key !== "Escape") {
                return;
            }
            menus.forEach(closeMenu);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initUserMenus);
        return;
    }

    initUserMenus();
})();
