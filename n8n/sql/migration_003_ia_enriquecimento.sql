-- Migracao IA: enriquecimento e risco automatizado
ALTER TABLE gastos_publicos_unificados
  ADD COLUMN IF NOT EXISTS categoria_ia TEXT,
  ADD COLUMN IF NOT EXISTS risco_ia TEXT,
  ADD COLUMN IF NOT EXISTS justificativa_ia TEXT;

CREATE INDEX IF NOT EXISTS idx_gastos_risco_ia ON gastos_publicos_unificados (risco_ia);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria_ia ON gastos_publicos_unificados (categoria_ia);
