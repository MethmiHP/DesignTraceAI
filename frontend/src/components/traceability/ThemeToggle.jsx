function ThemeToggle({
  darkMode,
  setDarkMode,
}) {
  return (
    <div className="theme-toggle-row">
      <span>
        {darkMode
          ? 'Dark Mode'
          : 'Light Mode'}
      </span>

      <button
        type="button"
        className={`theme-toggle ${
          darkMode ? 'on' : ''
        }`}
        onClick={() =>
          setDarkMode(
            (current) => !current,
          )
        }
        aria-label="Toggle dark and light mode"
      >
        <span className="toggle-circle" />
      </button>
    </div>
  )
}

export default ThemeToggle