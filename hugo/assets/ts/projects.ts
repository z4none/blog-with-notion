/**
 * Projects Page JavaScript
 * 处理项目页面的动画和交互效果
 */

class ProjectsManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupCarousels();
        this.setupScrollAnimations();
        this.setupFiltering();
        this.setupParallaxEffect();
    }

    /**
     * 设置轮播图功能
     */
    setupCarousels() {
        const carousels = document.querySelectorAll('.project-image-carousel');
        
        carousels.forEach((carousel, carouselIndex) => {
            const slides = carousel.querySelectorAll('.project-slide');
            const prevBtn = carousel.querySelector('.carousel-btn.prev');
            const nextBtn = carousel.querySelector('.carousel-btn.next');
            const indicators = carousel.querySelectorAll('.indicator');
            
            if (slides.length <= 1) return;

            let currentSlide = 0;
            let autoplayInterval;

            const showSlide = (index) => {
                slides.forEach(slide => slide.classList.remove('active'));
                indicators.forEach(indicator => indicator.classList.remove('active'));
                
                currentSlide = (index + slides.length) % slides.length;
                slides[currentSlide].classList.add('active');
                indicators[currentSlide]?.classList.add('active');
            };

            const nextSlide = () => showSlide(currentSlide + 1);
            const prevSlide = () => showSlide(currentSlide - 1);

            const startAutoplay = () => {
                autoplayInterval = setInterval(nextSlide, 4000);
            };

            const stopAutoplay = () => {
                clearInterval(autoplayInterval);
            };

            // 按钮事件
            prevBtn?.addEventListener('click', () => {
                prevSlide();
                stopAutoplay();
                startAutoplay();
            });

            nextBtn?.addEventListener('click', () => {
                nextSlide();
                stopAutoplay();
                startAutoplay();
            });

            // 指示器事件
            indicators.forEach((indicator, index) => {
                indicator.addEventListener('click', () => {
                    showSlide(index);
                    stopAutoplay();
                    startAutoplay();
                });
            });

            // 鼠标悬停暂停自动播放
            carousel.addEventListener('mouseenter', stopAutoplay);
            carousel.addEventListener('mouseleave', startAutoplay);

            // 开始自动播放
            startAutoplay();
        });
    }

    /**
     * 设置滚动动画
     */
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    
                    // 为项目卡片内的元素添加延迟动画
                    const cardInner = entry.target.querySelector('.project-card-inner');
                    if (cardInner) {
                        const elements = cardInner.querySelectorAll('.project-image-container, .project-content');
                        elements.forEach((el, index) => {
                            setTimeout(() => {
                                el.style.animation = `fadeInUp 0.6s ease-out ${index * 0.1}s both`;
                            }, 100);
                        });
                    }
                }
            });
        }, observerOptions);

        // 观察所有项目卡片
        document.querySelectorAll('.project-card').forEach(card => {
            observer.observe(card);
        });
    }

    /**
     * 设置项目筛选功能
     */
    setupFiltering() {
        // 创建筛选控制面板
        const header = document.querySelector('.projects-header');
        if (!header) return;

        const techTags = new Set();
        document.querySelectorAll('.tech-tag').forEach(tag => {
            techTags.add(tag.textContent.trim());
        });

        if (techTags.size === 0) return;

        // 创建筛选器HTML
        const filterHTML = `
            <div class="projects-filter">
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="all">全部项目</button>
                    ${Array.from(techTags).map(tech => 
                        `<button class="filter-btn" data-filter="${tech}">${tech}</button>`
                    ).join('')}
                </div>
            </div>
        `;

        header.insertAdjacentHTML('afterend', filterHTML);

        // 添加筛选器样式
        const filterStyles = `
            <style>
                .projects-filter {
                    text-align: center;
                    margin-bottom: 2rem;
                    animation: fadeInUp 0.8s ease-out 0.3s both;
                }
                
                .filter-buttons {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    justify-content: center;
                    align-items: center;
                }
                
                .filter-btn {
                    padding: 0.5rem 1rem;
                    border: 2px solid var(--primary-color);
                    background: transparent;
                    color: var(--primary-color);
                    border-radius: 2rem;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    font-size: 0.875rem;
                }
                
                .filter-btn:hover,
                .filter-btn.active {
                    background: var(--primary-color);
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
                }
                
                .project-card.hidden {
                    display: none;
                }
                
                .project-card.fade-out {
                    animation: fadeOut 0.3s ease-out forwards;
                }
                
                @keyframes fadeOut {
                    to {
                        opacity: 0;
                        transform: scale(0.9);
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', filterStyles);

        // 筛选逻辑
        const filterButtons = document.querySelectorAll('.filter-btn');
        const projectCards = document.querySelectorAll('.project-card');

        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const filter = btn.dataset.filter;
                
                // 更新按钮状态
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // 筛选项目卡片
                projectCards.forEach(card => {
                    const techTags = Array.from(card.querySelectorAll('.tech-tag')).map(tag => tag.textContent.trim());
                    
                    if (filter === 'all' || techTags.includes(filter)) {
                        card.classList.remove('hidden', 'fade-out');
                        setTimeout(() => {
                            card.style.animation = 'fadeInUp 0.6s ease-out forwards';
                        }, 50);
                    } else {
                        card.classList.add('fade-out');
                        setTimeout(() => {
                            card.classList.add('hidden');
                        }, 300);
                    }
                });
            });
        });
    }

    /**
     * 设置视差效果
     */
    setupParallaxEffect() {
        const handleScroll = () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.project-image-single img, .project-slide.active img');
            
            parallaxElements.forEach(el => {
                const speed = 0.5;
                const yPos = -(scrolled * speed);
                el.style.transform = `translateY(${yPos}px) scale(1.1)`;
            });
        };

        // 节流函数
        let ticking = false;
        const requestTick = () => {
            if (!ticking) {
                window.requestAnimationFrame(handleScroll);
                ticking = true;
                setTimeout(() => { ticking = false; }, 100);
            }
        };

        window.addEventListener('scroll', requestTick);
    }

    /**
     * 设置项目卡片3D效果
     */
    setup3DEffect() {
        document.querySelectorAll('.project-card').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
            });
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new ProjectsManager();
});

// 添加页面加载动画
window.addEventListener('load', () => {
    document.body.classList.add('page-loaded');
});

// 添加页面加载样式
const pageStyles = `
    <style>
        body:not(.page-loaded) .projects-header,
        body:not(.page-loaded) .projects-filter {
            opacity: 0;
        }
        
        body.page-loaded .projects-header,
        body.page-loaded .projects-filter {
            opacity: 1;
        }
        
        .animate-in {
            animation: fadeInUp 0.6s ease-out forwards;
        }
        
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', pageStyles);