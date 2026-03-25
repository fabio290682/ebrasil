-- Migracao para bases ja existentes
ALTER TABLE gastos_publicos_unificados
  ADD COLUMN IF NOT EXISTS categoria_origem TEXT,
  ADD COLUMN IF NOT EXISTS agente_publico TEXT,
  ADD COLUMN IF NOT EXISTS partido TEXT,
  ADD COLUMN IF NOT EXISTS tipo_despesa TEXT;

CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos_publicos_unificados (categoria_origem);
CREATE INDEX IF NOT EXISTS idx_gastos_agente ON gastos_publicos_unificados (agente_publico);
CREATE INDEX IF NOT EXISTS idx_gastos_partido ON gastos_publicos_unificados (partido);
