(function () {
    function initDailyTabs() {
        var tabsRoot = document.querySelector("[data-daily-tabs]");
        var panelsRoot = document.querySelector("[data-daily-sections]");
        if (!tabsRoot || !panelsRoot) {
            return;
        }

        var tabs = Array.prototype.slice.call(tabsRoot.querySelectorAll("[data-tab-key]"));
        var panels = Array.prototype.slice.call(panelsRoot.querySelectorAll("[data-section-key]"));
        if (!tabs.length || !panels.length) {
            return;
        }

        function getPanel(key) {
            return panels.find(function (panel) {
                return panel.dataset.sectionKey === key;
            });
        }

        function clearSectionParam() {
            var url = new URL(window.location.href);
            if (!url.searchParams.has("section")) {
                return;
            }

            url.searchParams.delete("section");
            var nextUrl = url.pathname + (url.search ? url.search : "") + url.hash;
            window.history.replaceState(window.history.state, "", nextUrl);
        }

        function setActiveTab(key) {
            var nextPanel = getPanel(key);
            if (!nextPanel) {
                return;
            }

            tabs.forEach(function (tab) {
                var isActive = tab.dataset.tabKey === key;
                tab.classList.toggle("is-active", isActive);
                tab.setAttribute("aria-selected", isActive ? "true" : "false");
            });

            panels.forEach(function (panel) {
                var isActive = panel.dataset.sectionKey === key;
                panel.classList.toggle("is-active", isActive);
                panel.hidden = !isActive;
                panel.setAttribute("aria-hidden", isActive ? "false" : "true");
            });
        }

        tabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                setActiveTab(tab.dataset.tabKey);
            });
        });

        clearSectionParam();

        var initialTab = tabs.find(function (tab) {
            return tab.classList.contains("is-active");
        }) || tabs[0];

        setActiveTab(initialTab.dataset.tabKey);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDailyTabs);
        return;
    }

    initDailyTabs();
})();
