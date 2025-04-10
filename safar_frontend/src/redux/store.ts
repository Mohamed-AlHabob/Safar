import { configureStore } from "@reduxjs/toolkit"
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from "redux-persist"
import { combineReducers } from "redux"
import { api } from "./services/api"
import authReducer from "./features/auth/auth-slice"
import modalReducer from "./features/ui/modal-slice"
import scrollReducer from "./features/ui/infinite-scroll-slice"
import storage from "@/lib/redux-persist-storage"

const rootReducer = combineReducers({
  [api.reducerPath]: api.reducer,
  auth: authReducer,
  modal: modalReducer,
  scroll: scrollReducer,
})

export const persistConfig = {
  key: "root",
  storage,
  whitelist: ["auth"],
  blacklist: [api.reducerPath],
  version: 1,
}

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer)

// Create store factory function
export const makeStore = () => {
  return configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(api.middleware),
    devTools: process.env.NODE_ENV !== "production",
  })
}

// Define types
export type AppStore = ReturnType<typeof makeStore>
export type RootState = ReturnType<AppStore["getState"]>
export type AppDispatch = AppStore["dispatch"]

// Create store instance
export const store = makeStore()
export const persistor = persistStore(store)