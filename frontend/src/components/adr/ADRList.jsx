function StatusBadge({ status }) {
  return (
    <span className={`adr-status adr-status-${status}`}>
      {status}
    </span>
  )
}

function ADRList({
  adrs,
  selectedADR,
  onSelect,
  search,
  onSearchChange,
}) {
  const filtered = adrs.filter((adr) => {
    const query = search.toLowerCase()

    return (
      adr.adr_id?.toLowerCase().includes(query) ||
      adr.title?.toLowerCase().includes(query) ||
      adr.status?.toLowerCase().includes(query)
    )
  })

  return (
    <aside className="adr-list-panel">
      <div className="adr-search-wrapper">
        <input
          className="adr-search"
          type="text"
          placeholder="Search ADRs..."
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </div>

      <div className="adr-list-heading">
        <span>Architecture Decision Records</span>
        <span>{filtered.length}</span>
      </div>

      <div className="adr-list">
        {filtered.length === 0 ? (
          <div className="adr-empty-list">
            No ADRs found.
          </div>
        ) : (
          filtered.map((adr) => (
            <button
              key={adr.adr_id}
              type="button"
              className={
                selectedADR?.adr_id === adr.adr_id
                  ? 'adr-list-item selected'
                  : 'adr-list-item'
              }
              onClick={() => onSelect(adr)}
            >
              <div className="adr-list-item-top">
                <span className="adr-id">
                  {adr.adr_id}
                </span>

                <StatusBadge status={adr.status} />
              </div>

              <strong>{adr.title}</strong>

              <span className="adr-list-date">
                {adr.created_at
                  ? new Date(adr.created_at).toLocaleDateString()
                  : 'No date'}
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  )
}

export default ADRList