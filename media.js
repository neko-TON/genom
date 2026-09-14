/* Photo story: keyboard navigation and optional, finite playback. */
(() => {
  'use strict';
  const story = document.querySelector('[data-photo-story]');
  if (!story) return;
  const tabs = [...story.querySelectorAll('[role="tab"]')];
  const panels = [...story.querySelectorAll('[role="tabpanel"]')];
  const play = story.querySelector('.story-play');
  const counter = story.querySelector('[data-story-count]');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let active = 0, timer = null, playing = false;
  function stop() {
    clearTimeout(timer);
    timer = null;
    playing = false;
    play.textContent = 'Play sequence';
    play.setAttribute('aria-pressed', 'false');
  }
  function select(index, focus = false) {
    active = index;
    tabs.forEach((tab, i) => {
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
      panels[i].classList.toggle('is-entering', i === index && !reduced.matches);
    });
    counter.textContent = `0${index + 1} / 03`;
    if (focus) tabs[index].focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => { stop(); select(index); });
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault(); stop(); select(next, true);
    });
  });
  function advance() {
    timer = setTimeout(() => {
      if (!playing || document.hidden || reduced.matches) { stop(); return; }
      if (active === tabs.length - 1) { stop(); return; }
      select(active + 1); advance();
    }, 4000);
  }
  play.addEventListener('click', () => {
    if (playing) { stop(); return; }
    select(0);
    playing = true;
    play.textContent = 'Pause sequence';
    play.setAttribute('aria-pressed', 'true');
    advance();
  });
  function motionPreference() { stop(); play.hidden = reduced.matches; }
  reduced.addEventListener('change', motionPreference);
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      if (!entries[0].isIntersecting) stop();
    }, { threshold: .1 }).observe(story);
  }
  motionPreference();
  select(0);
})();
