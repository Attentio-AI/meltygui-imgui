#pragma once
#include "imgui.h"
#include "imgui_internal.h"
#include <stdexcept>
#include <vector>
#include <memory>
#include <algorithm>
#include <string>

// A draw buffer and a temporary local layout scope, never an ImGui context.
// The host owns NewFrame/Render and all widget/keyboard/text-edit state.
namespace meltygui {
struct RetainedCapture;
inline RetainedCapture*& capture_top() {
    static thread_local RetainedCapture* value = nullptr;
    return value;
}
inline ImVec2 shifted(ImVec2 p, ImVec2 delta) { return ImVec2(p.x + delta.x, p.y + delta.y); }
inline void shift_rect(ImRect& rect, ImVec2 delta) {
    rect.Min = shifted(rect.Min, delta); rect.Max = shifted(rect.Max, delta);
}
inline bool frame_active() { return ImGui::GetCurrentContext() && GImGui->WithinFrameScope; }

struct RetainedCapture {
    ImGuiContext* context;
    ImDrawList draw;
    ImGuiWindow* window = nullptr;
    ImDrawList* parent_draw = nullptr;
    RetainedCapture* parent = nullptr;
    ImGuiWindowTempData layout;
    ImVector<ImGuiID> ids;
    ImVec2 origin, position, size, size_full, content, content_ideal, scroll;
    ImRect work, parent_work, inner, inner_clip, clip, content_region;
    ImVec2 mouse, mouse_previous, clicks[5];
    bool skip = false;
    bool active = false;
    int window_depth = 0;
    std::vector<std::unique_ptr<ImDrawList>> child_draws;
    std::vector<ImGuiWindow*> handled_children;
    int child_draw_count = 0;
    ImGuiStackSizes stack_sizes;
    ImGuiTable* table_at_begin = nullptr;
    ImGuiTabBar* tab_at_begin = nullptr;
    std::string scope_key;
    ImGuiID previous_alive = 0;
    ImGuiID child_active = 0;

    RetainedCapture(const char* key) : context(ImGui::GetCurrentContext()), draw(ImGui::GetDrawListSharedData()), scope_key(key) {
        if (!context) throw std::runtime_error("DrawCapture requires the host ImGui context");
    }
    ~RetainedCapture() {
        if (active && ImGui::GetCurrentContext() == context && capture_top() == this) end();
    }
    void nav_shift(ImVec2 screen_delta, ImVec2 relative_delta) {
        ImGuiContext& g = *context;
        shift_rect(g.NavScoringRect, screen_delta);
        for (int layer = 0; layer < ImGuiNavLayer_COUNT; ++layer)
            shift_rect(window->NavRectRel[layer], relative_delta);
        if (g.NavWindow == window) shift_rect(g.NavInitResultRectRel, relative_delta);
        ImGuiNavMoveResult* results[] = {&g.NavMoveResultLocal, &g.NavMoveResultLocalVisibleSet, &g.NavMoveResultOther};
        for (auto* result : results)
            if (result->Window == window) shift_rect(result->RectRel, relative_delta);
    }
    void begin(float width, float height, float x, float y) {
        if (active) throw std::runtime_error("Recursive capture of the same view");
        if (ImGui::GetCurrentContext() != context || !frame_active())
            throw std::runtime_error("DrawCapture must run inside its host's active frame");
        window = ImGui::GetCurrentWindow();
        parent = capture_top();
        origin = ImVec2(x, y);
        ImVec2 parent_origin = parent ? parent->origin : ImVec2(0, 0);
        ImVec2 delta(x - parent_origin.x, y - parent_origin.y);
        parent_draw = window->DrawList;
        window_depth = context->CurrentWindowStack.Size;
        stack_sizes.SetToCurrentState();
        table_at_begin = context->CurrentTable;
        tab_at_begin = context->CurrentTabBar;
        child_draw_count = 0;
        handled_children.clear();
        previous_alive = context->ActiveIdIsAlive;
        child_active = 0;
        context->ActiveIdIsAlive = 0;
        layout = window->DC;
        ids = window->IDStack;
        position = window->Pos; size = window->Size; size_full = window->SizeFull;
        content = window->ContentSize; content_ideal = window->ContentSizeIdeal;
        scroll = window->Scroll; skip = window->SkipItems;
        work = window->WorkRect; parent_work = window->ParentWorkRect;
        inner = window->InnerRect; inner_clip = window->InnerClipRect;
        clip = window->ClipRect; content_region = window->ContentRegionRect;
        ImGuiIO& io = context->IO;
        mouse = io.MousePos; mouse_previous = io.MousePosPrev;
        io.MousePos = shifted(mouse, ImVec2(-delta.x, -delta.y));
        io.MousePosPrev = shifted(mouse_previous, ImVec2(-delta.x, -delta.y));
        for (int i = 0; i < 5; ++i) {
            clicks[i] = io.MouseClickedPos[i];
            io.MouseClickedPos[i] = shifted(clicks[i], ImVec2(-delta.x, -delta.y));
        }
        nav_shift(ImVec2(-delta.x, -delta.y), ImVec2(position.x - delta.x, position.y - delta.y));
        draw._ResetForNewFrame();
        draw.PushTextureID(io.Fonts->TexID);
        draw.PushClipRect(ImVec2(0, 0), ImVec2(width, height), false);
        window->DrawList = &draw;
        window->Pos = ImVec2(0, 0);
        window->Size = window->SizeFull = ImVec2(width, height);
        window->ContentSize = window->ContentSizeIdeal = ImVec2(width, height);
        window->Scroll = ImVec2(0, 0);
        window->SkipItems = false;
        window->WorkRect = window->ParentWorkRect = window->InnerRect = window->InnerClipRect =
            window->ClipRect = window->ContentRegionRect = ImRect(0, 0, width, height);
        auto& dc = window->DC;
        dc.CursorPos = dc.CursorPosPrevLine = dc.CursorStartPos = dc.CursorMaxPos = dc.IdealMaxPos = ImVec2(0, 0);
        dc.CurrLineSize = dc.PrevLineSize = ImVec2(0, 0);
        dc.CurrLineTextBaseOffset = dc.PrevLineTextBaseOffset = 0;
        dc.Indent.x = dc.ColumnsOffset.x = dc.GroupOffset.x = 0;
        dc.ItemWidth = width * .65f;
        dc.TextWrapPos = -1;
        dc.LastItemId = 0; dc.LastItemStatusFlags = 0;
        dc.LastItemRect = dc.LastItemDisplayRect = ImRect();
        // Independent recapture must give widgets the same ID as nested capture.
        window->IDStack.resize(1);
        ImGui::PushID(scope_key.c_str());
        capture_top() = this;
        active = true;
    }
    // One retained view in a single call: the capture scope, the view's ID
    // scope and the group that measures its content.
    void begin_view(float width, float height, float x, float y, const char* label) {
        begin(width, height, x, y);
        ImGui::PushID(label);
        ImGui::BeginGroup();
    }
    // Close the group and ID scope and report the measured content size and
    // whether this view owns the live widget. With end_if_idle, a view without
    // a live widget also ends its capture here; the return value says whether
    // it did. Otherwise the caller reads item/input state and calls end().
    bool end_view(bool end_if_idle, float* width, float* height, bool* live) {
        if (!active || capture_top() != this || ImGui::GetCurrentContext() != context)
            throw std::runtime_error("Unbalanced DrawCapture scope");
        ImGui::EndGroup();
        ImGui::PopID();
        ImVec2 measured = ImGui::GetItemRectSize();
        *width = measured.x; *height = measured.y;
        *live = active_widget();
        if (end_if_idle && !*live) { end(); return true; }
        return false;
    }
    void detach_child(ImGuiWindow* child) {
        if (std::find(handled_children.begin(), handled_children.end(), child) != handled_children.end()) return;
        if (child->DrawList->IdxBuffer.Size) {
            if (child_draw_count == (int)child_draws.size())
                child_draws.emplace_back(new ImDrawList(ImGui::GetDrawListSharedData()));
            auto& copy = *child_draws[child_draw_count++];
            copy.CmdBuffer = child->DrawList->CmdBuffer;
            copy.IdxBuffer = child->DrawList->IdxBuffer;
            copy.VtxBuffer = child->DrawList->VtxBuffer;
            copy._PopUnusedDrawCmd();
            child->DrawList->_ResetForNewFrame();
        }
        child->Pos = shifted(child->Pos, origin);
        shift_rect(child->OuterRectClipped, origin);
        shift_rect(child->InnerRect, origin); shift_rect(child->InnerClipRect, origin);
        shift_rect(child->WorkRect, origin); shift_rect(child->ParentWorkRect, origin);
        shift_rect(child->ClipRect, origin); shift_rect(child->ContentRegionRect, origin);
        child->DC.CursorPos = shifted(child->DC.CursorPos, origin);
        child->DC.CursorPosPrevLine = shifted(child->DC.CursorPosPrevLine, origin);
        child->DC.CursorStartPos = shifted(child->DC.CursorStartPos, origin);
        child->DC.CursorMaxPos = shifted(child->DC.CursorMaxPos, origin);
        child->DC.IdealMaxPos = shifted(child->DC.IdealMaxPos, origin);
        for (auto* nested : child->DC.ChildWindows) detach_child(nested);
        handled_children.push_back(child);
    }
    int draw_count() const { return 1 + child_draw_count; }
    bool active_widget() const {
        return active && context->ActiveId && context->ActiveIdIsAlive == context->ActiveId
            && child_active != context->ActiveId;
    }
    ImDrawList* draw_at(int index) {
        if (index == 0) return &draw;
        if (index < 1 || index > child_draw_count) throw std::out_of_range("capture draw list");
        return child_draws[index - 1].get();
    }
    void restore_stacks(const ImGuiStackSizes& sizes) {
        while (context->FontStack.Size > sizes.SizeOfFontStack) ImGui::PopFont();
        while (context->ColorStack.Size > sizes.SizeOfColorStack) ImGui::PopStyleColor();
        while (context->StyleVarStack.Size > sizes.SizeOfStyleVarStack) ImGui::PopStyleVar();
        while (context->FocusScopeStack.Size > sizes.SizeOfFocusScopeStack) ImGui::PopFocusScope();
        while (context->GroupStack.Size > sizes.SizeOfGroupStack) ImGui::EndGroup();
    }
    void end() {
        if (!active || capture_top() != this || ImGui::GetCurrentContext() != context)
            throw std::runtime_error("Unbalanced DrawCapture scope");
        while (context->CurrentTable && context->CurrentTable != table_at_begin) ImGui::EndTable();
        while (context->CurrentTabBar && context->CurrentTabBar != tab_at_begin) ImGui::EndTabBar();
        while (context->CurrentWindowStack.Size > window_depth) {
            restore_stacks(context->CurrentWindow->DC.StackSizesOnBegin);
            if (context->CurrentWindow->Flags & ImGuiWindowFlags_ChildWindow) ImGui::EndChild();
            else ImGui::End();
        }
        restore_stacks(stack_sizes);
        if (parent && context->ActiveId && context->ActiveIdIsAlive == context->ActiveId)
            parent->child_active = context->ActiveId;
        if (!context->ActiveIdIsAlive && previous_alive == context->ActiveId)
            context->ActiveIdIsAlive = previous_alive;
        for (int i = layout.ChildWindows.Size; i < window->DC.ChildWindows.Size; ++i)
            detach_child(window->DC.ChildWindows[i]);
        if (parent) parent->handled_children.insert(parent->handled_children.end(), handled_children.begin(), handled_children.end());
        // Child windows remain part of the host frame's navigation/window tree.
        layout.ChildWindows = window->DC.ChildWindows;
        draw.PopClipRect();
        draw.PopTextureID();
        draw._PopUnusedDrawCmd();
        ImVec2 parent_origin = parent ? parent->origin : ImVec2(0, 0);
        ImVec2 delta(origin.x - parent_origin.x, origin.y - parent_origin.y);
        nav_shift(delta, ImVec2(delta.x - position.x, delta.y - position.y));
        auto& io = context->IO;
        io.MousePos = mouse; io.MousePosPrev = mouse_previous;
        for (int i = 0; i < 5; ++i) io.MouseClickedPos[i] = clicks[i];
        // Keep global navigation item counts, but restore the parent's layout.
        int nav_mask = window->DC.NavLayerActiveMaskNext;
        int regular = window->DC.FocusCounterRegular, tab = window->DC.FocusCounterTabStop;
        window->DrawList = parent_draw;
        window->DC = layout;
        window->DC.NavLayerActiveMaskNext |= nav_mask;
        window->DC.FocusCounterRegular = regular;
        window->DC.FocusCounterTabStop = tab;
        window->IDStack = ids;
        window->Pos = position; window->Size = size; window->SizeFull = size_full;
        window->ContentSize = content; window->ContentSizeIdeal = content_ideal;
        window->Scroll = scroll; window->SkipItems = skip;
        window->WorkRect = work; window->ParentWorkRect = parent_work;
        window->InnerRect = inner; window->InnerClipRect = inner_clip;
        window->ClipRect = clip; window->ContentRegionRect = content_region;
        capture_top() = parent;
        active = false;
    }
};
}
