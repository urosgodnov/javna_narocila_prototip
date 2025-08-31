"""
Lot manager for unified lot architecture.
Manages lot navigation, creation, and deletion.
Preserves EXACT visual design from current implementation.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from utils.form_helpers import FormContext


class LotManager:
    """
    Manages lot operations in the unified architecture.
    ALL forms have lots - minimum one "General" lot.
    Provides UI for lot navigation and management.
    """
    
    # Icons used in UI (preserve exact icons)
    ICONS = {
        'lot': '📦',
        'add': '➕',
        'delete': '🗑️',
        'left': '⬅️',
        'right': '➡️',
        'copy': '📋',
        'clear': '🗑️'
    }
    
    def __init__(self, context: FormContext):
        """
        Initialize lot manager.
        
        Args:
            context: FormContext instance
        """
        self.context = context
        
    def render_lot_navigation(self, 
                             style: str = 'tabs',
                             allow_add: bool = True,
                             allow_remove: bool = True,
                             max_lots: Optional[int] = None) -> None:
        """
        Render lot navigation UI.
        
        Args:
            style: Navigation style ('tabs', 'buttons', 'select')
            allow_add: Whether to allow adding new lots
            allow_remove: Whether to allow removing lots
            max_lots: Maximum number of lots allowed
        """
        lots = self.context.get_all_lots()
        current_lot_index = self.context.lot_index
        
        if style == 'tabs':
            self._render_tabs_navigation(lots, current_lot_index, allow_add, allow_remove, max_lots)
        elif style == 'buttons':
            self._render_buttons_navigation(lots, current_lot_index, allow_add, allow_remove, max_lots)
        elif style == 'select':
            self._render_select_navigation(lots, current_lot_index, allow_add, allow_remove, max_lots)
        else:
            # Default to tabs
            self._render_tabs_navigation(lots, current_lot_index, allow_add, allow_remove, max_lots)
    
    def _render_tabs_navigation(self, 
                               lots: List[Dict], 
                               current_index: int,
                               allow_add: bool,
                               allow_remove: bool,
                               max_lots: Optional[int]) -> None:
        """Render tabs-style lot navigation."""
        # Create tab labels with lot icon
        tab_labels = [f"{self.ICONS['lot']} {lot['name']}" for lot in lots]
        
        # Add "+" tab if allowed
        if allow_add and (max_lots is None or len(lots) < max_lots):
            tab_labels.append(f"{self.ICONS['add']} Add Lot")
        
        # Render tabs
        selected_tab = st.tabs(tab_labels)
        
        # Handle tab selection
        for idx, tab in enumerate(selected_tab):
            with tab:
                if idx < len(lots):
                    # Existing lot tab
                    if idx != current_index:
                        # Switch to this lot
                        if st.button(f"Preklopi na {lots[idx]['name']}", key=f"switch_lot_{idx}"):
                            self.context.switch_to_lot(idx)
                            st.rerun()
                    else:
                        # Current lot - show lot info and controls
                        self._render_lot_controls(idx, lots[idx], allow_remove)
                else:
                    # Add lot tab
                    self._render_add_lot_form()
    
    def _render_buttons_navigation(self, 
                                  lots: List[Dict], 
                                  current_index: int,
                                  allow_add: bool,
                                  allow_remove: bool,
                                  max_lots: Optional[int]) -> None:
        """Render button-style lot navigation."""
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Previous button
            if current_index > 0:
                if st.button(f"{self.ICONS['left']} Prejšnji", key="prev_lot"):
                    self.context.switch_to_lot(current_index - 1)
                    st.rerun()
        
        with col2:
            # Current lot display
            current_lot = lots[current_index] if current_index < len(lots) else lots[0]
            st.markdown(
                f"<h3 style='text-align: center;'>{self.ICONS['lot']} {current_lot['name']} ({current_index + 1}/{len(lots)})</h3>",
                unsafe_allow_html=True
            )
        
        with col3:
            # Next button
            if current_index < len(lots) - 1:
                if st.button(f"Naslednji {self.ICONS['right']}", key="next_lot"):
                    self.context.switch_to_lot(current_index + 1)
                    st.rerun()
        
        # Lot controls below navigation
        st.divider()
        col_add, col_remove, col_rename = st.columns(3)
        
        with col_add:
            if allow_add and (max_lots is None or len(lots) < max_lots):
                if st.button(f"{self.ICONS['add']} Dodaj sklop", key="add_lot_btn"):
                    self._show_add_lot_dialog()
        
        with col_remove:
            if allow_remove and len(lots) > 1:
                if st.button(f"{self.ICONS['delete']} Odstrani sklop", key="remove_lot_btn"):
                    self.remove_current_lot()
        
        with col_rename:
            if st.button(f"✏️ Preimenuj sklop", key="rename_lot_btn"):
                self._show_rename_dialog()
    
    def _render_select_navigation(self, 
                                 lots: List[Dict], 
                                 current_index: int,
                                 allow_add: bool,
                                 allow_remove: bool,
                                 max_lots: Optional[int]) -> None:
        """Render select-box style lot navigation."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Select box for lot selection
            lot_options = [f"{self.ICONS['lot']} {lot['name']}" for lot in lots]
            selected = st.selectbox(
                "Izberi sklop",
                options=lot_options,
                index=current_index,
                key="lot_selector"
            )
            
            # Get selected index
            selected_idx = lot_options.index(selected)
            if selected_idx != current_index:
                self.context.switch_to_lot(selected_idx)
                st.rerun()
        
        with col2:
            # Lot actions menu
            actions = []
            if allow_add and (max_lots is None or len(lots) < max_lots):
                actions.append(f"{self.ICONS['add']} Add Lot")
            if allow_remove and len(lots) > 1:
                actions.append(f"{self.ICONS['delete']} Remove Current")
            actions.append("✏️ Rename Current")
            actions.append(f"{self.ICONS['copy']} Duplicate Current")
            actions.append(f"{self.ICONS['clear']} Clear Current")
            
            action = st.selectbox("Dejanja", options=["Izberi dejanje..."] + actions, key="lot_actions")
            
            if action and action != "Izberi dejanje...":
                if "Dodaj sklop" in action:
                    self._show_add_lot_dialog()
                elif "Remove Current" in action:
                    self.remove_current_lot()
                elif "Rename Current" in action:
                    self._show_rename_dialog()
                elif "Duplicate Current" in action:
                    self.duplicate_current_lot()
                elif "Clear Current" in action:
                    self.clear_current_lot()
    
    def _render_lot_controls(self, 
                            lot_index: int, 
                            lot_info: Dict,
                            allow_remove: bool) -> None:
        """Render controls for the current lot."""
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                st.info(f"Indeks sklopa: {lot_index}")
            
            with col2:
                if allow_remove and self.context.get_lot_count() > 1:
                    if st.button(f"{self.ICONS['delete']} Odstrani ta sklop", key=f"remove_{lot_index}"):
                        self.context.remove_lot(lot_index)
                        st.rerun()
            
            with col3:
                if st.button("✏️ Preimenuj", key=f"rename_{lot_index}"):
                    self._show_rename_dialog()
    
    def _render_add_lot_form(self) -> None:
        """Render form for adding a new lot."""
        with st.form("add_lot_form"):
            st.markdown("### Add New Lot")
            
            new_lot_name = st.text_input(
                "Ime sklopa",
                placeholder="Vnesite ime sklopa (neobvezno)",
                key="new_lot_name_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                copy_from = st.selectbox(
                    "Kopiraj podatke iz",
                    options=["Prazno"] + [lot['name'] for lot in self.context.get_all_lots()],
                    key="copy_from_select"
                )
            
            with col2:
                submit = st.form_submit_button(f"{self.ICONS['add']} Dodaj sklop")
            
            if submit:
                # Add the new lot
                new_index = self.add_lot(new_lot_name if new_lot_name else None)
                
                # Copy data if requested
                if copy_from != "Prazno":
                    source_lots = self.context.get_all_lots()
                    for idx, lot in enumerate(source_lots):
                        if lot['name'] == copy_from:
                            self.context.copy_lot_data(idx, new_index)
                            break
                
                # Switch to new lot
                self.context.switch_to_lot(new_index)
                st.rerun()
    
    def _show_add_lot_dialog(self) -> None:
        """Show dialog for adding a lot (used in button/select styles)."""
        # Use session state to show/hide dialog
        if 'show_add_lot_dialog' not in st.session_state:
            st.session_state['show_add_lot_dialog'] = False
        
        st.session_state['show_add_lot_dialog'] = True
        st.rerun()
    
    def _show_rename_dialog(self) -> None:
        """Show dialog for renaming current lot."""
        current_lot = self.context.get_current_lot()
        
        with st.form("rename_lot_form"):
            new_name = st.text_input(
                "New Name",
                value=current_lot['name'],
                key="rename_lot_input"
            )
            
            if st.form_submit_button("Preimenuj"):
                self.context.rename_lot(self.context.lot_index, new_name)
                st.rerun()
    
    def add_lot(self, name: Optional[str] = None) -> int:
        """
        Add a new lot.
        
        Args:
            name: Optional lot name
            
        Returns:
            Index of the new lot
        """
        return self.context.add_lot(name)
    
    def remove_current_lot(self) -> bool:
        """
        Remove the current lot (if more than one exists).
        
        Returns:
            True if removed, False if cannot remove
        """
        if self.context.get_lot_count() > 1:
            result = self.context.remove_lot(self.context.lot_index)
            if result:
                st.rerun()
            return result
        else:
            st.warning("Zadnjega sklopa ni mogoče odstraniti. Obstajati mora vsaj en sklop.")
            return False
    
    def duplicate_current_lot(self) -> int:
        """
        Duplicate the current lot with all its data.
        
        Returns:
            Index of the new lot
        """
        current_lot = self.context.get_current_lot()
        new_name = f"{current_lot['name']} (Copy)"
        
        # Add new lot
        new_index = self.context.add_lot(new_name)
        
        # Copy data
        self.context.copy_lot_data(self.context.lot_index, new_index)
        
        # Switch to new lot
        self.context.switch_to_lot(new_index)
        st.rerun()
        
        return new_index
    
    def clear_current_lot(self) -> None:
        """Clear all data in the current lot."""
        if st.confirm("Are you sure you want to clear all data in this lot?"):
            self.context.clear_lot_data(self.context.lot_index)
            st.rerun()
    
    def render_lot_summary(self) -> None:
        """Render a summary of all lots with their data counts."""
        lots = self.context.get_all_lots()
        
        st.markdown("### Lot Summary")
        
        for lot in lots:
            lot_data = self.context.get_lot_data(lot['index'])
            field_count = len(lot_data)
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                icon = "✅" if lot['index'] == self.context.lot_index else ""
                st.markdown(f"{self.ICONS['lot']} **{lot['name']}** {icon}")
            
            with col2:
                st.text(f"{field_count} fields")
            
            with col3:
                if lot['index'] != self.context.lot_index:
                    if st.button("Preklopi", key=f"switch_summary_{lot['index']}"):
                        self.context.switch_to_lot(lot['index'])
                        st.rerun()
    
    def get_lot_navigation_state(self) -> Dict[str, Any]:
        """
        Get current navigation state for persistence.
        
        Returns:
            Dictionary with navigation state
        """
        return {
            'current_lot_index': self.context.lot_index,
            'lot_count': self.context.get_lot_count(),
            'current_lot_name': self.context.get_current_lot()['name']
        }