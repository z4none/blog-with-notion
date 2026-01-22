/**
 * Projects Page Interactive Logic
 * Handles filtering by status and technology, and animations.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const projectsGrid = document.getElementById('projects-grid');
    const projectCards = document.querySelectorAll('.project-card');
    const typeFiltersContainer = document.getElementById('type-filters');
    const techFiltersContainer = document.getElementById('tech-filters');
    const emptyState = document.getElementById('empty-state');

    // State
    let currentFilter = {
        type: 'all',
        tech: 'all'
    };

    // 1. Initialize
    initTypeFilters();
    initTechFilters();

    /**
     * Initialize Project Type filters
     */
    function initTypeFilters() {
        // Collect unique project types
        const typeSet = new Set();
        console.log('Scanning project cards for types...');
        projectCards.forEach(card => {
            const type = card.dataset.projectType;
            console.log('Card type found:', type);
            if (type) typeSet.add(type);
        });

        // Create "All" button
        const allBtn = createFilterButton('all', '全部', true, 'type');
        typeFiltersContainer.appendChild(allBtn);

        // Create buttons for each type
        Array.from(typeSet).sort().forEach(type => {
            const btn = createFilterButton(type, type, false, 'type');
            typeFiltersContainer.appendChild(btn);
        });
    }

    /**
     * Initialize technology filters
     */
    function initTechFilters() {
        const technologySet = new Set();
        const techCount = {};

        // Extract technologies from all cards
        projectCards.forEach(card => {
            const techTags = card.querySelectorAll('.project-tag-badge');
            techTags.forEach(tag => {
                const tech = tag.textContent.trim();
                technologySet.add(tech);
                techCount[tech] = (techCount[tech] || 0) + 1;
            });
        });

        // Sort by count (descending)
        const sortedTechs = Array.from(technologySet).sort((a, b) => {
            return techCount[b] - techCount[a];
        });

        // Add "All" button
        const allBtn = createFilterButton('all', '全部', true, 'tech');
        techFiltersContainer.appendChild(allBtn);

        // Add tech buttons
        sortedTechs.forEach(tech => {
            const btn = createFilterButton(tech, `${tech}`, false, 'tech');
            techFiltersContainer.appendChild(btn);
        });
    }

    /**
     * Genetic Filter Button Creator
     * @param {string} value - The filter value (e.g., 'python' or 'Personal Project')
     * @param {string} label - The display label
     * @param {boolean} isActive - Initial active state
     * @param {string} filterType - 'type' or 'tech'
     */
    function createFilterButton(value, label, isActive, filterType) {
        const btn = document.createElement('button');
        btn.className = `filter-btn ${isActive ? 'active' : ''}`;
        btn.dataset.value = value;
        btn.textContent = label;

        btn.addEventListener('click', () => {
            // Toggle active class on siblings within the same container
            const container = filterType === 'type' ? typeFiltersContainer : techFiltersContainer;
            const siblings = container.querySelectorAll('.filter-btn');
            siblings.forEach(s => s.classList.remove('active'));
            btn.classList.add('active');

            // Update state
            currentFilter[filterType] = value;
            applyFilters();
        });

        return btn;
    }

    /**
     * Apply all filters (Type AND Tech)
     */
    function applyFilters() {
        let visibleCount = 0;

        projectCards.forEach(card => {
            // 1. Check Type
            const cardType = card.dataset.projectType;
            const typeMatch = currentFilter.type === 'all' || cardType === currentFilter.type;

            // 2. Check Tech
            const cardTechs = Array.from(card.querySelectorAll('.project-tag-badge')).map(t => t.textContent.trim());
            const techMatch = currentFilter.tech === 'all' || cardTechs.includes(currentFilter.tech);

            // Final Visibility (AND logic)
            if (typeMatch && techMatch) {
                card.classList.remove('hidden');
                // Re-trigger animation
                card.style.animation = 'none';
                card.offsetHeight; /* trigger reflow */
                card.style.animation = 'fadeInUp 0.5s ease-out forwards';
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        // Show/Hide Empty State
        if (visibleCount === 0) {
            emptyState.style.display = 'block';
            projectsGrid.style.display = 'none';
        } else {
            emptyState.style.display = 'none';
            projectsGrid.style.display = 'grid';
        }
    }
});

// Ensure the animation used by JS exists and behaves correctly
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
`;
document.head.appendChild(styleSheet);

