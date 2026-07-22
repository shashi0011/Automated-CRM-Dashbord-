import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api';

const blankDraft = {
  hcp_name: null, hcp_specialty: null, hcp_hospital: null,
  interaction_type: null, interaction_date: null,
  topics_discussed: null, products_discussed: null,
  materials_shared: null, samples_distributed: null,
  summary: null, sentiment: null,
  follow_up_required: null, follow_up_notes: null, follow_up_date: null,
  compliance_flag: null, compliance_notes: null,
};

export const fetchDraft = createAsyncThunk('interactions/fetchDraft', async (sessionId) => {
  return api.getDraft(sessionId);
});

export const submitDraft = createAsyncThunk('interactions/submitDraft', async (sessionId, { dispatch }) => {
  const result = await api.submitDraft(sessionId);
  dispatch(fetchSubmittedInteractions());
  return result;
});

export const resetDraft = createAsyncThunk('interactions/resetDraft', async (sessionId) => {
  return api.resetDraft(sessionId);
});

export const fetchSubmittedInteractions = createAsyncThunk(
  'interactions/fetchSubmitted',
  async () => api.listInteractions()
);

export const updateSubmittedInteraction = createAsyncThunk(
  'interactions/updateSubmitted',
  async ({ id, payload }) => api.updateInteraction(id, payload)
);

export const deleteSubmittedInteraction = createAsyncThunk(
  'interactions/deleteSubmitted',
  async (id) => {
    await api.deleteInteraction(id);
    return id;
  }
);

const initialState = {
  draft: blankDraft,
  submittedInteractions: [],
  status: 'idle',
  error: null,
};

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState,
  reducers: {
    setDraft(state, action) {
      state.draft = { ...state.draft, ...action.payload };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDraft.fulfilled, (state, action) => {
        state.draft = action.payload;
      })
      .addCase(submitDraft.fulfilled, (state) => {
        state.draft = blankDraft;
      })
      .addCase(resetDraft.fulfilled, (state, action) => {
        state.draft = action.payload;
      })
      .addCase(fetchSubmittedInteractions.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchSubmittedInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.submittedInteractions = action.payload;
      })
      .addCase(updateSubmittedInteraction.fulfilled, (state, action) => {
        const idx = state.submittedInteractions.findIndex((i) => i.id === action.payload.id);
        if (idx >= 0) state.submittedInteractions[idx] = action.payload;
      })
      .addCase(deleteSubmittedInteraction.fulfilled, (state, action) => {
        state.submittedInteractions = state.submittedInteractions.filter(
          (i) => i.id !== action.payload
        );
      });
  },
});

export const { setDraft } = interactionsSlice.actions;
export default interactionsSlice.reducer;
